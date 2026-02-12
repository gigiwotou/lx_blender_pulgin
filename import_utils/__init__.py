import os
from typing import List, Dict, Tuple


class LXObject:
    def __init__(self):
        self.skin_name = ""
        self.verts = []
        self.faces = []
        self.uvs = []
        self.mats = []
        self.face_mat = []
        # 骨骼权重数据
        self.bone_v_count = []  # 每个顶点受影响的骨骼数量
        self.bone_ids = []  # 每个顶点的骨骼ID列表
        self.weight_array = []  # 每个顶点的权重列表


class LXBone:
    """骨骼数据结构"""

    def __init__(self):
        self.bone_name = ""
        self.bone_id = 0
        self.parent_name = ""
        self.parent_id = -1
        self.vpos = [0.0, 0.0, 0.0]  # 位置
        self.vrot = [0.0, 0.0, 0.0, 1.0]  # 四元数旋转 (w, x, y, z)
        self.children = 0
        self.bone_type = 1  # 1=bone, 2=dummey


class BNCReader:
    """BNC骨骼文件读取器"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.bones: List[LXBone] = []
        self.bone_count = 0
        self.dummey_count = 0

    def read_bnc(self) -> Tuple[List[LXBone], int, int]:
        """读取BNC文件，返回(骨骼列表, 骨骼数, 虚拟体数)"""
        print(f"[BNC] 开始读取BNC文件: {self.filepath}")

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            print(f"[BNC] 使用UTF-8编码读取，共 {len(lines)} 行")
        except Exception as e:
            print(f"[BNC] UTF-8读取失败: {e}，尝试GBK编码")
            with open(self.filepath, "r", encoding="gbk") as f:
                lines = f.readlines()
            print(f"[BNC] 使用GBK编码读取，共 {len(lines)} 行")

        i = 0
        # 读取骨骼数量
        print("[BNC] 开始查找骨骼数量...")
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("#"):
                i += 1
                continue
            if line.startswith("Bones:"):
                parts = line.split()
                print(f"[BNC] 找到骨骼数量行: {line}")
                if len(parts) >= 4:
                    self.bone_count = int(parts[1])
                    self.dummey_count = int(parts[3])
                    print(
                        f"[BNC] 骨骼数: {self.bone_count}, 虚拟体数: {self.dummey_count}"
                    )
                i += 1
                break
            i += 1

        # 读取每个骨骼
        print("[BNC] 开始读取骨骼数据...")
        bone_count = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("#") or not line:
                i += 1
                continue

            if line.startswith("bone ") or line.startswith("Dummey "):
                bone_count += 1
                bone = LXBone()
                parts = line.split()
                if len(parts) >= 2:
                    bone.bone_name = parts[1]
                    bone.bone_type = 1 if line.startswith("bone ") else 2
                    print(
                        f"[BNC] 读取骨骼[{bone_count}]: {bone.bone_name}, 类型: {'bone' if bone.bone_type == 1 else 'Dummey'}"
                    )

                # 读取骨骼块内容
                i += 1
                while i < len(lines):
                    inner_line = lines[i].strip()
                    if inner_line == "}":
                        i += 1
                        break

                    inner_parts = inner_line.split()
                    if len(inner_parts) >= 2:
                        key = inner_parts[0]
                        if key == "parent":
                            bone.parent_name = inner_parts[1]
                        elif key == "pivot":
                            bone.vpos = [
                                float(inner_parts[1]),
                                float(inner_parts[2]),
                                float(inner_parts[3]),
                            ]
                        elif key == "quaternion":
                            # BNC文件格式: w x y z (4个浮点数)
                            # 3dsmax中: quat x y z w
                            # Blender中: Quaternion((w, x, y, z))
                            # 所以BNC的 [w, x, y, z] 直接对应 Blender的 (w, x, y, z)
                            w = float(inner_parts[1])
                            x = float(inner_parts[2])
                            y = float(inner_parts[3])
                            z = float(inner_parts[4])
                            bone.vrot = [
                                w,
                                x,
                                y,
                                z,
                            ]  # 存储为 [w, x, y, z] 供Blender使用
                        elif key == "children":
                            bone.children = int(inner_parts[1])

                    i += 1

                self.bones.append(bone)
            else:
                i += 1

        print(f"[BNC] 共读取 {len(self.bones)} 块骨骼")

        # 建立父子关系
        print("[BNC] 建立父子关系...")

        # 首先按类型分组统计
        bone_count = sum(1 for b in self.bones if b.bone_type == 1)
        dummey_count = sum(1 for b in self.bones if b.bone_type == 2)
        print(f"[BNC] 骨骼数量: {bone_count}, 虚拟体数量: {dummey_count}")

        for bone in self.bones:
            if bone.parent_name and bone.parent_name != "NULL":
                parent_found = False

                # 特殊处理：虚拟体（dummey）的parentName格式可能是 b数字 或 d数字
                if bone.bone_type == 2 and len(bone.parent_name) >= 2:
                    prefix = bone.parent_name[0]
                    rest = bone.parent_name[1:]

                    if prefix == "b" and rest.isdigit():
                        # b13 格式：表示第13块骨骼（从0开始的索引）
                        # 注意：3dsmax中索引从0开始，所以 b13 就是第13块（索引13）
                        bone_idx = int(rest)
                        if bone_idx < len(self.bones):
                            bone.parent_id = bone_idx
                            bone.parent_name = self.bones[bone_idx].bone_name
                            parent_found = True
                            print(
                                f"[BNC] {bone.bone_name} 的父级是 {bone.parent_name} (索引b{rest})"
                            )

                    elif prefix == "d" and rest.isdigit():
                        # d3 格式：表示第3个虚拟体
                        # 虚拟体在数组中的实际索引 = 骨骼数 + 虚拟体序号
                        dummey_idx = int(rest)
                        actual_idx = bone_count + dummey_idx
                        if actual_idx < len(self.bones):
                            bone.parent_id = actual_idx
                            bone.parent_name = self.bones[actual_idx].bone_name
                            parent_found = True
                            print(
                                f"[BNC] {bone.bone_name} 的父级是 {bone.parent_name} (索引d{rest} = ID {actual_idx})"
                            )

                # 如果不是虚拟体的特殊格式，或特殊格式处理失败，则用名称匹配
                if not parent_found:
                    for idx, parent_bone in enumerate(self.bones):
                        if parent_bone.bone_name == bone.parent_name:
                            bone.parent_id = idx
                            parent_found = True
                            print(
                                f"[BNC] {bone.bone_name} 的父级是 {bone.parent_name} (名称匹配 ID: {idx})"
                            )
                            break

                if not parent_found:
                    # 父骨骼未找到
                    print(
                        f"[BNC] 警告: {bone.bone_name} 的父骨骼 '{bone.parent_name}' 未找到，作为根骨骼处理"
                    )
                    bone.parent_name = "NULL"

        print(f"[BNC] BNC文件读取完成，返回 {len(self.bones)} 块骨骼")
        return self.bones, self.bone_count, self.dummey_count


def read_bnc(filepath: str) -> Tuple[List[LXBone], int, int]:
    reader = BNCReader(filepath)
    return reader.read_bnc()


class SKCReader:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def read_skc(self) -> List[LXObject]:
        objects = []

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except:
            with open(self.filepath, "r", encoding="gbk") as f:
                lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith("Static Skin "):
                parts = line.split()
                if len(parts) >= 3:
                    obj = LXObject()
                    obj.skin_name = parts[2]

                    i += 1
                    objects.append(obj)

                    while i < len(lines) and not lines[i].strip().startswith(
                        "Vertices:"
                    ):
                        i += 1

                    if i >= len(lines):
                        break

                    parts_v = lines[i].split()
                    num_vert = 0
                    for j, p in enumerate(parts_v):
                        if p == "Vertices:" and j + 1 < len(parts_v):
                            try:
                                num_vert = int(parts_v[j + 1])
                            except:
                                pass
                            break

                    i += 1

                    for v in range(num_vert):
                        if i >= len(lines):
                            break

                        line_v = lines[i].strip()

                        if line_v.startswith("v "):
                            parts_vtx = line_v.split()
                            if len(parts_vtx) >= 7:
                                try:
                                    x = float(parts_vtx[1])
                                    y = float(parts_vtx[2])
                                    z = float(parts_vtx[3])
                                    obj.verts.append([x, y, z])
                                    obj.uvs.append(
                                        [float(parts_vtx[5]), float(parts_vtx[6]), 0]
                                    )

                                    # 解析骨骼权重
                                    # 格式: v x y z vt u v Bones N bone_id weight ...
                                    if "Bones" in parts_vtx:
                                        bones_idx = parts_vtx.index("Bones")
                                        if bones_idx + 1 < len(parts_vtx):
                                            bone_count = int(parts_vtx[bones_idx + 1])
                                            obj.bone_v_count.append(bone_count)

                                            vert_bone_ids = []
                                            vert_weights = []

                                            for b in range(bone_count):
                                                idx = bones_idx + 2 + b * 2
                                                if idx + 1 < len(parts_vtx):
                                                    bone_id = int(parts_vtx[idx])
                                                    weight = float(parts_vtx[idx + 1])
                                                    vert_bone_ids.append(bone_id)
                                                    vert_weights.append(weight)

                                            obj.bone_ids.append(vert_bone_ids)
                                            obj.weight_array.append(vert_weights)
                                        else:
                                            obj.bone_v_count.append(0)
                                            obj.bone_ids.append([])
                                            obj.weight_array.append([])
                                    else:
                                        obj.bone_v_count.append(0)
                                        obj.bone_ids.append([])
                                        obj.weight_array.append([])
                                except:
                                    pass

                        i += 1

                    while i < len(lines):
                        line_f = lines[i].strip()

                        if line_f.startswith("f "):
                            parts_f = line_f.split()
                            # SKC格式: f mat_id v1 v2 v3 ...
                            # 3dsmax脚本: subline[4], [5], [6] (1-based)
                            # Python中: parts_f[3], [4], [5] (0-based)
                            if len(parts_f) >= 6:
                                try:
                                    # 取顶点索引 (0-based)
                                    v1 = int(parts_f[3])
                                    v2 = int(parts_f[4])
                                    v3 = int(parts_f[5])
                                    obj.faces.append([v1, v2, v3])
                                except:
                                    pass

                        i += 1

                    break

            i += 1

        return objects


def read_skc(filepath: str) -> List[LXObject]:
    reader = SKCReader(filepath)
    return reader.read_skc()


class GMCReader:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.objects = []
        self.materials = []
        self.textures = []

    def read_gmc(self):
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except:
            with open(self.filepath, "r", encoding="gbk") as f:
                content = f.read()

        lines = content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            if line.startswith("Textures"):
                try:
                    num_tex = int(line.split()[1])
                    i += 1
                    for _ in range(num_tex):
                        if i < len(lines):
                            self.textures.append(lines[i].strip())
                            i += 1
                except:
                    i += 1
                continue

            if line.startswith("Shaders"):
                try:
                    num_shaders = int(line.split()[1])
                    i += 1
                    for _ in range(num_shaders):
                        shader = {}
                        while i < len(lines) and lines[i].strip() != "}":
                            parts = lines[i].strip().split()
                            if parts:
                                if parts[0] == "Texture":
                                    shader["tex_id"] = int(parts[1])
                                    shader["tex_type"] = (
                                        parts[2] if len(parts) > 2 else "NORMAL"
                                    )
                                elif parts[0] == "TwoSide":
                                    shader["twoside"] = (
                                        parts[1] if len(parts) > 1 else "0"
                                    )
                                elif parts[0] == "Blend":
                                    shader["blend"] = " ".join(parts[1:])
                                elif parts[0] == "Opaque":
                                    shader["opaque"] = (
                                        float(parts[1]) if len(parts) > 1 else 1.0
                                    )
                            i += 1
                        self.materials.append(shader)
                        i += 1
                except:
                    i += 1
                continue

            if line.startswith("SceneObjects"):
                try:
                    parts = line.split()
                    if len(parts) >= 2:
                        num_objects = int(parts[1])
                        i += 1
                        for _ in range(num_objects):
                            if i < len(lines) and lines[i].strip().startswith("Object"):
                                obj_name = lines[i].strip().split()[1]
                                i += 1
                                obj = LXObject()
                                obj.skin_name = obj_name

                                while i < len(lines) and lines[i].strip() != "}":
                                    line_inner = lines[i].strip()
                                    parts_inner = line_inner.split()

                                    if parts_inner and parts_inner[0].startswith(
                                        "Vertices"
                                    ):
                                        try:
                                            parts_v = line_inner.split()
                                            num_vert = int(parts_v[1])
                                            num_face = int(parts_v[3])
                                            i += 1

                                            for _ in range(num_vert):
                                                if i < len(lines):
                                                    parts_data = lines[i].split()
                                                    if len(parts_data) >= 17:
                                                        try:
                                                            x = float(parts_data[1])
                                                            y = float(parts_data[2])
                                                            z = float(parts_data[3])
                                                            u = float(parts_data[14])
                                                            v = float(parts_data[15])
                                                            obj.verts.append([x, y, z])
                                                            obj.uvs.append([u, v, 0, 0])
                                                        except:
                                                            pass
                                                    i += 1

                                            for _ in range(num_face):
                                                if i < len(lines):
                                                    parts_f = lines[i].split()
                                                    if len(parts_f) >= 8:
                                                        try:
                                                            mat_id = int(parts_f[1])
                                                            v1 = int(parts_f[2])
                                                            v2 = int(parts_f[3])
                                                            v3 = int(parts_f[4])
                                                            obj.face_mat.append(mat_id)
                                                            obj.faces.append(
                                                                [v1, v2, v3]
                                                            )
                                                        except:
                                                            pass
                                                    i += 1
                                        except:
                                            i += 1
                                    else:
                                        i += 1

                                self.objects.append(obj)
                            else:
                                i += 1
                except:
                    i += 1
            else:
                i += 1

        return self.objects, self.materials, self.textures


class GMBReader:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.objects = []
        self.materials = []
        self.textures = []

    def read_gmb(self):
        import struct

        def read_string(f, max_len=256):
            """读取字符串，尝试多种编码"""
            try:
                data = f.read(4)
                if len(data) < 4:
                    return None
                str_len = struct.unpack("<I", data)[0]
                if str_len == 0:
                    return ""
                if str_len > max_len:
                    return None
                data = f.read(str_len)
                if len(data) < str_len:
                    return None
                for encoding in ["utf-8", "gbk", "latin1", "cp1252"]:
                    try:
                        return data.decode(encoding).strip("\x00")
                    except:
                        continue
                return data.decode("utf-8", errors="ignore").strip("\x00")
            except:
                return None

        try:
            with open(self.filepath, "rb") as f:
                # 读取文件头
                header = f.read(10)
                if header[:4] != b"GMDL":
                    raise ValueError("不是有效的GMB文件")

                # 读取纹理
                tex_num = struct.unpack("<I", f.read(4))[0]
                for _ in range(tex_num):
                    tex_name = read_string(f)
                    if tex_name:
                        self.textures.append(tex_name)

                # 读取材质
                shader_num = struct.unpack("<I", f.read(4))[0]
                for _ in range(shader_num):
                    shader = {}
                    shader["tex_id"] = struct.unpack("<I", f.read(4))[0]
                    shader["tex_type"] = read_string(f)
                    shader["twoside"] = f.read(1)[0]
                    shader["blend"] = read_string(f)
                    shader["opaque"] = struct.unpack("<f", f.read(4))[0]
                    self.materials.append(shader)

                # 读取对象数量
                obj_num = struct.unpack("<I", f.read(4))[0]
                # 跳过辅助数据
                f.read(4)  # dummy_num
                f.read(4)  # total_verts
                f.read(4)  # total_faces

                for obj_idx in range(obj_num):
                    obj = LXObject()
                    obj.skin_name = read_string(f) or f"Object_{obj_idx}"

                    # 读取顶点和面数量
                    vert_num = struct.unpack("<I", f.read(4))[0]
                    face_num = struct.unpack("<I", f.read(4))[0]

                    # 读取顶点 (36字节每个)
                    for _ in range(vert_num):
                        # 位置 (12字节)
                        vx = struct.unpack("<f", f.read(4))[0]
                        vy = struct.unpack("<f", f.read(4))[0]
                        vz = struct.unpack("<f", f.read(4))[0]
                        # 法线 (12字节)
                        f.read(12)
                        # 颜色 (4字节)
                        f.read(4)
                        # UV (8字节)
                        tu = struct.unpack("<f", f.read(4))[0]
                        tv = struct.unpack("<f", f.read(4))[0]

                        obj.verts.append([vx, vy, vz])
                        obj.uvs.append([tu, tv, 0])

                    # 读取面 (28字节每个)
                    # 格式: 材质ID(long) + 3个顶点索引(long) + 3个法线float
                    for _ in range(face_num):
                        mat_id = struct.unpack("<I", f.read(4))[0]
                        v1 = struct.unpack("<I", f.read(4))[0]
                        v2 = struct.unpack("<I", f.read(4))[0]
                        v3 = struct.unpack("<I", f.read(4))[0]
                        # 跳过面法线 (12字节)
                        f.read(12)

                        obj.face_mat.append(mat_id)
                        obj.faces.append([v1, v2, v3])

                    self.objects.append(obj)

                return self.objects, self.materials, self.textures
        except Exception as e:
            import traceback

            traceback.print_exc()
            raise Exception(f"读取GMB文件失败: {e}")


class AMBReader:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.bones = 30
        self.dummies = 6
        self.frames = 0
        self.animations = []

    def read_amb(self):
        import struct

        try:
            with open(self.filepath, "rb") as f:
                header = f.read(5)
                if header != b"BANIM":
                    raise ValueError("不是有效的AMB文件")

                self.bones = struct.unpack("<I", f.read(4))[0]
                self.dummies = struct.unpack("<I", f.read(4))[0]
                self.frames = struct.unpack("<I", f.read(4))[0]

                for i in range(self.frames):
                    frame_data = []
                    try:
                        for j in range(self.bones + self.dummies):
                            anim_data = {}

                            try:
                                if j == 0:
                                    anim_data["pos"] = [
                                        struct.unpack("<f", f.read(4))[0],
                                        struct.unpack("<f", f.read(4))[0],
                                        struct.unpack("<f", f.read(4))[0],
                                    ]
                                anim_data["rot"] = [
                                    struct.unpack("<f", f.read(4))[0],
                                    struct.unpack("<f", f.read(4))[0],
                                    struct.unpack("<f", f.read(4))[0],
                                    struct.unpack("<f", f.read(4))[0],
                                ]
                            except:
                                anim_data["rot"] = [0, 0, 0, 1]
                                if j == 0:
                                    anim_data["pos"] = [0, 0, 0]

                            frame_data.append(anim_data)

                        self.animations.append(frame_data)
                    except:
                        break

                return self.animations, self.bones, self.dummies
        except Exception as e:
            raise Exception(f"读取AMB文件失败: {e}")
