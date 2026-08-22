from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from flask import current_app

from redtail_repository import db
from redtail_repository.models import (
    Author,
    Device,
    DeviceCategory,
    DeviceDoc,
    DeviceFramework,
    LaboratoryExercise,
    LaboratoryExerciseCategory,
    LaboratoryExerciseDoc,
    LaboratoryExerciseImage,
    LaboratoryExerciseLevel,
    Simulation,
    SimulationCategory,
    SimulationDeviceDocument,
    SimulationDoc,
    SimulationImage,
    User,
)


def make_user(login: str, *, role: str = "user", verified: bool = False) -> User:
    user = User(login=login, name=login.replace("-", " ").title(), verified=verified)
    user.role = role
    user.set_password("test-password")
    return user


def seed_catalog():
    fixed_time = datetime(2024, 1, 15, 12, 0, 0)
    public_root = Path(current_app.config["PUBLIC_FOLDER"])
    docs_root = public_root / "docs"
    docs_root.mkdir(parents=True, exist_ok=True)
    (docs_root / "simulation.md").write_text(
        "# Simulation guide\n\n![Local](/static/img/NES.png)", encoding="utf-8"
    )
    (docs_root / "device.md").write_text("# Device guide", encoding="utf-8")
    (docs_root / "exercise.md").write_text("# Exercise guide", encoding="utf-8")

    author = Author(
        login="author", name="Example Author", link="https://example.test/author"
    )
    admin = make_user("admin-user", role="admin", verified=True)
    instructor = make_user("verified-instructor", role="instructor", verified=True)
    student = make_user("student-user", verified=False)

    device_category = DeviceCategory(name="Microcontroller", slug="microcontroller")
    device = Device(
        name="Test Board",
        slug="test-board",
        description="A deterministic test device.",
        cover_image_url="/static/img/NES.png",
    )
    framework = DeviceFramework(name="Native", slug="native", device=device)
    device.device_categories.append(device_category)
    device_doc = DeviceDoc(
        device=device,
        title="Device Guide",
        description="Device documentation",
        doc_url="public/docs/device.md",
    )

    simulation_category = SimulationCategory(name="Digital Twin", slug="digital-twin")
    simulation = Simulation(
        name="Test Simulation",
        slug="test-simulation",
        description="A deterministic simulation.",
        cover_image_url="/static/img/NES.png",
        video_url="",
    )
    simulation.authors.append(author)
    simulation.devices.append(device)
    simulation.device_frameworks.append(framework)
    simulation.simulation_categories.append(simulation_category)
    simulation.simulation_device_categories.append(device_category)
    simulation_doc = SimulationDoc(
        simulation=simulation,
        title="Simulation Guide",
        description="Simulation documentation",
        doc_url="public/docs/simulation.md",
    )
    simulation_device_doc = SimulationDeviceDocument(
        simulation=simulation,
        device=device,
        name="Board Guide",
        doc_url="public/docs/device.md",
    )
    simulation_image = SimulationImage(
        simulation=simulation,
        image_url="/static/img/NES.png",
        title="Simulation preview",
        description="Preview image",
    )

    exercise_category = LaboratoryExerciseCategory(
        name="Fundamentals", slug="fundamentals"
    )
    level = LaboratoryExerciseLevel(name="Introductory", slug="introductory")
    exercise = LaboratoryExercise(
        name="Test Exercise",
        slug="test-exercise",
        short_description="A deterministic laboratory exercise.",
        long_description="Long exercise description.",
        learning_goals="Learn deterministic testing.",
        cover_image_url="/static/img/NES.png",
        video_url="",
        active=True,
    )
    exercise.authors.append(author)
    exercise.simulations.append(simulation)
    exercise.laboratory_exercise_categories.append(exercise_category)
    exercise.device_frameworks.append(framework)
    exercise.levels.append(level)
    exercise_doc = LaboratoryExerciseDoc(
        laboratory_exercise=exercise,
        title="Exercise Guide",
        description="Public exercise documentation",
        doc_url="public/docs/exercise.md",
        is_solution=False,
    )
    solution_doc = LaboratoryExerciseDoc(
        laboratory_exercise=exercise,
        title="Exercise Solution",
        description="Instructor-only solution",
        doc_url="private/solution.md",
        is_solution=True,
    )
    exercise_image = LaboratoryExerciseImage(
        laboratory_exercise=exercise,
        image_url="/static/img/NES.png",
        title="Exercise preview",
        description="Preview image",
    )

    inactive_exercise = LaboratoryExercise(
        name="Inactive Exercise",
        slug="inactive-exercise",
        short_description="Not published.",
        active=False,
    )

    dated_records = (
        device_category,
        device,
        framework,
        device_doc,
        simulation_category,
        simulation,
        simulation_doc,
        simulation_device_doc,
        simulation_image,
        exercise_category,
        level,
        exercise,
        exercise_doc,
        solution_doc,
        exercise_image,
        inactive_exercise,
    )
    for record in dated_records:
        if hasattr(record, "last_updated"):
            record.last_updated = fixed_time
        if hasattr(record, "created_at"):
            record.created_at = fixed_time
        if hasattr(record, "updated_at"):
            record.updated_at = fixed_time

    db.session.add_all(
        [
            admin,
            instructor,
            student,
            device_doc,
            simulation_doc,
            simulation_device_doc,
            simulation_image,
            exercise_doc,
            solution_doc,
            exercise_image,
            inactive_exercise,
        ]
    )
    db.session.commit()

    return SimpleNamespace(
        author=author,
        admin=admin,
        instructor=instructor,
        student=student,
        device_category=device_category,
        device=device,
        framework=framework,
        device_doc=device_doc,
        simulation_category=simulation_category,
        simulation=simulation,
        simulation_doc=simulation_doc,
        simulation_device_doc=simulation_device_doc,
        simulation_image=simulation_image,
        exercise_category=exercise_category,
        level=level,
        exercise=exercise,
        exercise_doc=exercise_doc,
        solution_doc=solution_doc,
        exercise_image=exercise_image,
        inactive_exercise=inactive_exercise,
    )
