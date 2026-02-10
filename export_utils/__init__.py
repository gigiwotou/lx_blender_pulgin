import math
import struct
import os
from typing import List, Dict, Tuple


class FMCWriter:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def write(self, objects: List, frame_count: int, fps: float = 60):
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write("# GModel Animation File V1.0\n")
            f.write("# Model For Lxres.com Creation Time\n")
            f.write(f"SceneObjects {len(objects)} DummeyObjects 0\n")
            f.write(f"FPS {fps} Frames {frame_count} Mode: RIGID\n")

            pass

            for frame in range(frame_count):
                bpy.context.scene.frame_set(frame)
                f.write(f"frame {frame}\n{{\n")

                for obj in objects:
                    pos = obj.location
                    rot = obj.rotation_quaternion

                    if len(rot) < 4:
                        rot = [1.0, 0.0, 0.0, 0.0]

                    f.write(
                        f"  t {pos.x:.4f} {pos.y:.4f} {pos.z:.4f} q {rot[0]:.4f} {rot[1]:.4f} {rot[2]:.4f} {rot[3]:.4f}\n"
                    )

                f.write("}\n")


class POSWriter:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def write(self, frame_count: int):
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write("pose\n{\n")
            f.write(f"  start 0\n")
            f.write(f"  end {frame_count - 1}\n")
            f.write("}\n")


class GMBWriter:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def write(self, objects: List, materials: List, textures: List):
        with open(self.filepath, "wb") as f:
            header = b"GMDL V1.00"
            f.write(header)

            f.write(struct.pack("<I", len(textures)))
            for tex in textures:
                tex_bytes = tex.encode("utf-8")
                f.write(struct.pack("<I", len(tex_bytes)))
                f.write(tex_bytes)

            f.write(struct.pack("<I", len(materials)))
            for mat in materials:
                f.write(struct.pack("<I", mat["tex_id"]))
                tex_type = mat.get("tex_type", "NORMAL").encode("utf-8")
                f.write(struct.pack("<I", len(tex_type)))
                f.write(tex_type)
                f.write(bytes([mat.get("twoside", 0)]))
                blend = mat.get("blend", "DISABLE 1 0").encode("utf-8")
                f.write(struct.pack("<I", len(blend)))
                f.write(blend)
                f.write(struct.pack("<f", mat.get("opaque", 1.0)))

            f.write(struct.pack("<I", len(objects)))
            f.write(struct.pack("<I", 0))

            total_verts = sum(
                len(obj.verts) if hasattr(obj, "verts") else len(obj.data.vertices)
                for obj in objects
            )
            total_faces = sum(
                len(obj.faces) if hasattr(obj, "faces") else len(obj.data.polygons)
                for obj in objects
            )
            f.write(struct.pack("<I", total_verts))
            f.write(struct.pack("<I", total_faces))

            for obj in objects:
                name = obj.name.encode("utf-8")
                f.write(struct.pack("<I", len(name)))
                f.write(name)

                if hasattr(obj, "verts"):
                    verts = obj.verts
                    faces = obj.faces
                else:
                    mesh = obj.data
                    verts = [v.co for v in mesh.vertices]
                    faces = [p.vertices for p in mesh.polygons]

                f.write(struct.pack("<I", len(verts)))
                f.write(struct.pack("<I", len(faces)))

                for v in verts:
                    f.write(struct.pack("<6f", v[0], v[1], v[2], 0, 0, 0))
                    f.write(b"\xff\xff\xff\xff")
                    f.write(struct.pack("<2f", 0, 0))

                for face in faces:
                    if len(face) >= 3:
                        f.write(struct.pack("<4I", 0, face[0], face[1], face[2]))
                        f.write(struct.pack("<3f", 0, 0, 1))


class DESWriter:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def write(self, objects: List):
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write("# GModel Geometry File V1.0\n")
            f.write("# Model For Lxres.com Creation Time\n")
            f.write(f"SceneObjects {len(objects)} DummeyObjects 0\n")

            for obj in objects:
                pos = obj.location
                rot = obj.rotation_quaternion

                if len(rot) < 4:
                    rot = [1.0, 0.0, 0.0, 0.0]

                f.write(f"Object {obj.name}\n{{\n")
                f.write(f"  Position: {pos.x:.5f} {pos.y:.5f} {pos.z:.5f}\n")
                f.write(
                    f"  Quaternion: {rot[0]:.5f} {rot[1]:.5f} {rot[2]:.5f} {rot[3]:.5f}\n"
                )
                f.write("  TextureAnimation: 0 0.0 0.0\n")
                f.write("  Custom:\n  {\n  }\n")
                f.write("}\n")


class WPWriter:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def write(self, waypoints: List):
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(f"WayPoints {len(waypoints)}\n")

            for wp in waypoints:
                f.write(
                    f"Pos {wp['pos'][0]:.3f} {wp['pos'][1]:.3f} {wp['pos'][2]:.3f}\n"
                )
                f.write(f"Size {wp['size']}\n")
                f.write(f"Link {len(wp['links'])}\n")
                for link in wp["links"]:
                    f.write(f"{link['index']} {link['flag']} {link['dist']:.3f}\n")


class AMBWriter:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def write(self, animations: List, bones: int = 30, dummies: int = 6):
        with open(self.filepath, "wb") as f:
            header = b"BANIM"
            f.write(header)
            f.write(struct.pack("<I", bones))
            f.write(struct.pack("<I", dummies))
            f.write(struct.pack("<I", len(animations)))
            f.write(struct.pack("<I", 30))

            dummy_names = [
                b"\x00",
                b"b13\x00\x00",
                b"d3\x00\x00\x00",
                b"b17\x00\x00",
                b"d5\x00\x00\x00",
                b"b25\x00\x00",
            ]

            for i, frame in enumerate(animations):
                f.write(struct.pack("<I", -1))
                f.write(struct.pack("<I", i))

                for j in range(bones + dummies):
                    if j < len(frame):
                        anim = frame[j]
                        if j == 0 and "pos" in anim:
                            f.write(
                                struct.pack(
                                    "<3f",
                                    anim["pos"][0],
                                    anim["pos"][1],
                                    anim["pos"][2],
                                )
                            )
                        f.write(
                            struct.pack(
                                "<4f",
                                anim["rot"][0],
                                anim["rot"][1],
                                anim["rot"][2],
                                anim["rot"][3],
                            )
                        )

                        if j >= bones and j < bones + dummies:
                            name = (
                                dummy_names[j - bones]
                                if j - bones < len(dummy_names)
                                else b"\x00"
                            )
                            f.write(name)
                            f.write(struct.pack("<7f", 0, 0, 0, 1, 0, 0, 0))
                    else:
                        f.write(struct.pack("<7f", 0, 0, 0, 1, 0, 0, 0))
