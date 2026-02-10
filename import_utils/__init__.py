import os
from typing import List


class LXObject:
    def __init__(self):
        self.skin_name = ""
        self.verts = []
        self.faces = []
        self.uvs = []
        self.mats = []
        self.face_mat = []


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
                                    obj.uvs.append([float(parts_vtx[5]), 0, 0])
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

        try:
            with open(self.filepath, "rb") as f:
                header = f.read(10)
                if header[:4] != b"GMDL":
                    raise ValueError("不是有效的GMB文件")

                tex_num = struct.unpack("<I", f.read(4))[0]
                for _ in range(tex_num):
                    str_len = struct.unpack("<I", f.read(4))[0]
                    tex_name = f.read(str_len).decode("utf-8")
                    self.textures.append(tex_name)

                shader_num = struct.unpack("<I", f.read(4))[0]
                for _ in range(shader_num):
                    shader = {}
                    shader["tex_id"] = struct.unpack("<I", f.read(4))[0]
                    str_len = struct.unpack("<I", f.read(4))[0]
                    shader["tex_type"] = f.read(str_len).decode("utf-8")
                    shader["twoside"] = f.read(1)[0]
                    str_len = struct.unpack("<I", f.read(4))[0]
                    shader["blend"] = f.read(str_len).decode("utf-8")
                    shader["opaque"] = struct.unpack("<f", f.read(4))[0]
                    self.materials.append(shader)

                obj_num = struct.unpack("<I", f.read(4))[0]

                for _ in range(obj_num):
                    str_len = struct.unpack("<I", f.read(4))[0]
                    obj_name = f.read(str_len).decode("utf-8")

                    obj = LXObject()
                    obj.skin_name = obj_name

                    vert_num = struct.unpack("<I", f.read(4))[0]
                    face_num = struct.unpack("<I", f.read(4))[0]

                    for _ in range(vert_num):
                        try:
                            vx = struct.unpack("<f", f.read(4))[0]
                            vy = struct.unpack("<f", f.read(4))[0]
                            vz = struct.unpack("<f", f.read(4))[0]
                            nx = struct.unpack("<f", f.read(4))[0]
                            ny = struct.unpack("<f", f.read(4))[0]
                            nz = struct.unpack("<f", f.read(4))[0]
                            r = f.read(1)[0]
                            g = f.read(1)[0]
                            b = f.read(1)[0]
                            a = f.read(1)[0]
                            tu = struct.unpack("<f", f.read(4))[0]
                            tv = struct.unpack("<f", f.read(4))[0]

                            obj.verts.append([vx, vy, vz])
                            obj.uvs.append([tu, tv, 0, 0])
                        except:
                            break

                    for _ in range(face_num):
                        try:
                            mat_id = struct.unpack("<I", f.read(4))[0]
                            v1 = struct.unpack("<I", f.read(4))[0]
                            v2 = struct.unpack("<I", f.read(4))[0]
                            v3 = struct.unpack("<I", f.read(4))[0]

                            obj.face_mat.append(mat_id)
                            obj.faces.append([v1, v2, v3])
                        except:
                            break

                    self.objects.append(obj)

            return self.objects, self.materials, self.textures
        except Exception as e:
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
