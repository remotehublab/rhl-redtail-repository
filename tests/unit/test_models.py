import pytest
from sqlalchemy.exc import IntegrityError

from redtail_repository import db
from redtail_repository.models import (
    Device,
    DeviceCategory,
    DeviceFramework,
    LaboratoryExercise,
    LaboratoryExerciseCategory,
    LaboratoryExerciseLevel,
    Simulation,
    SimulationCategory,
    SimulationDeviceDocument,
    SimulationDoc,
    User,
)


def test_user_password_round_trip(app):
    user = User(login="someone", name="Someone", verified=False)
    user.set_password("correct horse battery staple")

    assert user.password_hash != "correct horse battery staple"
    assert user.check_password("correct horse battery staple")
    assert not user.check_password("wrong")


def test_model_strings_and_slug_properties(app, catalog):
    assert str(catalog.author) == "Example Author"
    assert str(catalog.exercise) == "Test Exercise"
    assert str(catalog.device) == "Test Board"
    assert str(catalog.level) == "Introductory"
    assert str(catalog.simulation) == "Test Simulation"
    assert str(catalog.exercise_category) == "Fundamentals"
    assert str(catalog.device_category) == "Microcontroller"
    assert str(catalog.framework) == "Native of Test Board"
    assert str(catalog.simulation_category) == "Digital Twin"
    assert catalog.simulation_doc.slugified_title == "simulation-guide"
    assert catalog.simulation_device_doc.slugified_name == "board-guide"


def test_relationships_are_bidirectional(app, catalog):
    assert catalog.exercise in catalog.author.laboratory_exercises
    assert catalog.simulation in catalog.author.simulations
    assert catalog.exercise in catalog.simulation.laboratory_exercises
    assert catalog.simulation in catalog.device.simulations
    assert catalog.framework in catalog.exercise.device_frameworks
    assert catalog.framework in catalog.simulation.device_frameworks
    assert catalog.device_doc in catalog.device.device_documents
    assert catalog.simulation_device_doc in catalog.device.simulation_documents


def test_owned_children_are_deleted_with_parents(app, catalog):
    exercise_id = catalog.exercise.id
    image_id = catalog.exercise_image.id
    doc_id = catalog.exercise_doc.id
    db.session.delete(catalog.exercise)
    db.session.commit()

    assert db.session.get(LaboratoryExercise, exercise_id) is None
    from redtail_repository.models import LaboratoryExerciseDoc, LaboratoryExerciseImage

    assert db.session.get(LaboratoryExerciseImage, image_id) is None
    assert db.session.get(LaboratoryExerciseDoc, doc_id) is None


@pytest.mark.parametrize(
    ("model", "kwargs"),
    [
        (Device, {"name": "D", "slug": "d", "description": "desc"}),
        (DeviceCategory, {"name": "C", "slug": "c"}),
        (LaboratoryExerciseCategory, {"name": "LC", "slug": "lc"}),
        (LaboratoryExerciseLevel, {"name": "L", "slug": "l"}),
        (SimulationCategory, {"name": "SC", "slug": "sc"}),
        (Simulation, {"name": "S", "slug": "s", "description": "desc"}),
    ],
)
def test_name_or_slug_uniqueness_is_enforced(app, model, kwargs):
    db.session.add_all([model(**kwargs), model(**kwargs)])
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_framework_children_are_deleted_with_device(app):
    device = Device(name="Board", slug="board", description="desc")
    framework = DeviceFramework(name="Native", slug="board-native", device=device)
    db.session.add(device)
    db.session.commit()
    framework_id = framework.id

    db.session.delete(device)
    db.session.commit()
    assert db.session.get(DeviceFramework, framework_id) is None


def test_document_properties_slugify_unicode(app):
    simulation = Simulation(name="S", slug="s", description="desc")
    device = Device(name="D", slug="d", description="desc")
    doc = SimulationDoc(simulation=simulation, title="Café Guide", doc_url="guide.md")
    device_doc = SimulationDeviceDocument(
        simulation=simulation, device=device, name="Board #1", doc_url="board.md"
    )
    assert doc.slugified_title == "cafe-guide"
    assert device_doc.slugified_name == "board-1"


def test_material_audit_fields_cover_every_document_type(app, catalog):
    documents = (
        catalog.exercise_doc,
        catalog.simulation_doc,
        catalog.device_doc,
        catalog.simulation_device_doc,
    )

    for document in documents:
        assert document.created_at is not None
        assert document.updated_at is not None
        assert document.uploaded_by_user_id is None
        assert document.updated_by_user_id is None

        document.mark_created_by(catalog.instructor)
        document.mark_updated_by(catalog.admin)

    db.session.commit()

    for document in documents:
        db.session.refresh(document)
        assert document.uploaded_by_user_id == catalog.instructor.id
        assert document.uploaded_by_user is catalog.instructor
        assert document.updated_by_user_id == catalog.admin.id
        assert document.updated_by_user is catalog.admin
