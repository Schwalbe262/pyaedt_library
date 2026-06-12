"""MFT geometry helpers."""


def create_core(design, name="core", core_material="ferrite"):
    main = design.modeler.create_box(
        origin=["-(4*l1+2*l2)/2", "-w1/2", "-(h1+2*l1)/2"],
        sizes=["4*l1+2*l2", "w1", "h1+2*l1"],
        name=name,
        material=core_material,
    )
    sub1 = design.modeler.create_box(
        origin=["-l1", "-w1/2", "-h1/2"],
        sizes=["-l2", "w1", "h1"],
        name=f"{name}_sub1",
        material=core_material,
    )
    sub2 = design.modeler.create_box(
        origin=["l1", "-w1/2", "-h1/2"],
        sizes=["l2", "w1", "h1"],
        name=f"{name}_sub2",
        material=core_material,
    )
    design.modeler.subtract([main], [sub1, sub2], keep_originals=False)
    return main


def create_coil(
    design,
    name,
    window_height,
    window_length,
    window_layer,
    N_input,
    width_fill_factor,
    space_length,
    space_width,
    shape="circle",
    offset=None,
    color=None,
):
    offset = offset or [0, 0, 0]
    n_turns = N_input
    shape = shape.lower()

    if shape == "circle":
        if window_layer > 1:
            coil_width = window_length * width_fill_factor / window_layer
            coil_height = coil_width
        else:
            coil_width = window_length
            coil_height = coil_width
        coil_gap_x = (window_length - coil_width * window_layer) / (window_layer - 1) if window_layer > 1 else 0
        coil_gap_z = (window_height - coil_width * n_turns) / (n_turns - 1) if n_turns > 1 else 0
    elif shape == "rectangle":
        coil_width = window_length * width_fill_factor / window_layer
        coil_height = window_height / n_turns
        coil_gap_x = (window_length - coil_width * window_layer) / (window_layer - 1) if window_layer > 1 else 0
        coil_gap_z = (window_height - coil_height * n_turns) / (n_turns - 1) if n_turns > 1 else 0
    else:
        raise ValueError("shape must be 'circle' or 'rectangle'")

    x_pos = [space_length / 2 + coil_width * (i + 0.5) + coil_gap_x * i for i in range(window_layer)]
    y_pos = [space_width / 2 + coil_width * (i + 0.5) + coil_gap_x * i for i in range(window_layer)]
    z_pos = [window_height / 2 - coil_height * (i + 0.5) - coil_gap_z * i for i in range(n_turns)]

    windings = []
    for i, (x, y) in enumerate(zip(x_pos, y_pos)):
        for j, z in enumerate(z_pos):
            points = [
                [f"{x}mm + {offset[0]}mm", f"{y}mm + {offset[1]}mm", f"{z}mm + {offset[2]}mm"],
                [f"{-x}mm + {offset[0]}mm", f"{y}mm + {offset[1]}mm", f"{z}mm + {offset[2]}mm"],
                [f"{-x}mm + {offset[0]}mm", f"{-y}mm + {offset[1]}mm", f"{z}mm + {offset[2]}mm"],
                [f"{x}mm + {offset[0]}mm", f"{-y}mm + {offset[1]}mm", f"{z}mm + {offset[2]}mm"],
                [f"{x}mm + {offset[0]}mm", f"{y}mm + {offset[1]}mm", f"{z}mm + {offset[2]}mm"],
            ]
            winding = design.modeler.create_polyline(
                points=points,
                name=f"{name}_{i}_{j}",
                material="copper",
                xsection_orient="Auto",
                xsection_type=shape,
                xsection_width=coil_width,
                xsection_height=coil_height,
                xsection_num_seg=6,
                xsection_topwidth=coil_width,
            )
            if color is not None:
                winding.color = color
            windings.append(winding)

    return windings, n_turns, coil_width, coil_height, coil_gap_x, coil_gap_z


def create_coil_section(design, winding_obj, sheet_prefix=None, plane="ZX", rename_faces=False, mod="both"):
    modeler = design.modeler

    def to_obj_list(obj_or_list):
        if isinstance(obj_or_list, (list, tuple, set)):
            return list(obj_or_list)
        return [obj_or_list]

    def center_x(obj):
        bounding_box = getattr(obj, "bounding_box", None)
        if bounding_box and len(bounding_box) == 6:
            return (float(bounding_box[0]) + float(bounding_box[3])) / 2.0
        return 0.0

    def rename_object_safe(obj, target_name, used_names):
        current_name = getattr(obj, "name", None)
        if not current_name:
            return None
        candidate = target_name
        if candidate != current_name:
            idx = 1
            while candidate in used_names:
                candidate = f"{target_name}_{idx}"
                idx += 1
        obj.name = candidate
        used_names.discard(current_name)
        used_names.add(candidate)
        return candidate

    winding_objs = to_obj_list(winding_obj)
    if not winding_objs:
        raise ValueError("winding_obj is empty")

    if sheet_prefix is None:
        first_name = getattr(winding_objs[0], "name", "winding")
        sheet_prefix = f"{first_name}_sec"

    before_sheet_names = set(modeler.sheet_names)
    ok = modeler.section(winding_objs, plane)
    if not ok:
        raise RuntimeError("section failed")

    after_sheet_names = set(modeler.sheet_names)
    new_sheet_names = sorted(after_sheet_names - before_sheet_names)
    sheets = [modeler.get_object_from_name(name) for name in new_sheet_names]

    before_sep_sheet_names = set(modeler.sheet_names)
    separated = modeler.separate_bodies(assignment=sheets)
    after_sep_sheet_names = set(modeler.sheet_names)
    new_sep_sheet_names = sorted(after_sep_sheet_names - before_sep_sheet_names)

    face_candidates = []
    if isinstance(separated, list):
        face_candidates.extend(separated)
    for name in new_sep_sheet_names:
        obj = modeler.get_object_from_name(name)
        if obj is not None:
            face_candidates.append(obj)
    face_candidates.extend(sheets)

    faces = []
    seen = set()
    for obj in face_candidates:
        if obj is None:
            continue
        obj_name = getattr(obj, "name", None)
        if not obj_name or obj_name in seen:
            continue
        seen.add(obj_name)
        faces.append(obj)

    if mod == "single":
        return [face.name for face in faces]

    x_small_faces = []
    x_large_faces = []
    used = set()
    for src in winding_objs:
        src_name = str(getattr(src, "name", src)).lower()
        group = [face for face in faces if src_name in str(getattr(face, "name", "")).lower()]
        if len(group) >= 2:
            group_sorted = sorted(group, key=center_x)
            x_small_faces.append(group_sorted[0])
            x_large_faces.append(group_sorted[-1])
            used.add(group_sorted[0].name)
            used.add(group_sorted[-1].name)

    remaining = [face for face in faces if getattr(face, "name", "") not in used]
    remaining_sorted = sorted(remaining, key=center_x)
    for i in range(0, len(remaining_sorted) - 1, 2):
        x_small_faces.append(remaining_sorted[i])
        x_large_faces.append(remaining_sorted[i + 1])

    if rename_faces:
        used_names = set(modeler.object_names)
        pair_count = min(len(x_small_faces), len(x_large_faces))
        for i in range(pair_count):
            base = sheet_prefix if pair_count == 1 else f"{sheet_prefix}_{i + 1}"
            rename_object_safe(x_small_faces[i], f"{base}_neg", used_names)
            rename_object_safe(x_large_faces[i], f"{base}_pos", used_names)

    return [face.name for face in x_small_faces], [face.name for face in x_large_faces]
