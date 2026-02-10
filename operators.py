import bpy
import os
from . import import_utils
from . import export_utils


class SKC_OT_import(bpy.types.Operator):
    """导入流星SKC人物模型"""

    bl_idname = "lx.import_skc"
    bl_label = "导入SKC模型"
    bl_options = {"PRESET"}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.skc", options={"HIDDEN"})
    bnc_path: bpy.props.StringProperty(
        name="BNC骨骼文件", default="", subtype="FILE_PATH"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "bnc_path")

    def execute(self, context):
        try:
            skc_path = self.filepath

            print(f"[LX] 开始导入: {os.path.basename(skc_path)}")

            objects = import_utils.read_skc(skc_path)

            print(f"[LX] 解析完成，对象数: {len(objects)}")

            if len(objects) == 0:
                print(f"[LX] 错误: 没有解析出对象")
                self.report({"ERROR"}, "未能解析SKC文件")
                return {"CANCELLED"}

            obj_data = objects[0]
            print(f"[LX] 对象名: {obj_data.skin_name}")
            print(f"[LX] 顶点数: {len(obj_data.verts)}")
            print(f"[LX] 面数: {len(obj_data.faces)}")

            if len(obj_data.verts) == 0:
                print(f"[LX] 错误: 没有顶点数据")
                self.report({"ERROR"}, "没有顶点数据")
                return {"CANCELLED"}

            # 检查顶点索引范围
            max_idx = 0
            for face in obj_data.faces:
                for idx in face:
                    if idx > max_idx:
                        max_idx = idx
            print(f"[LX] 最大顶点索引: {max_idx}")
            print(f"[LX] 顶点总数: {len(obj_data.verts)}")

            bpy.ops.object.select_all(action="DESELECT")

            mesh = bpy.data.meshes.new(obj_data.skin_name)
            mesh.from_pydata(obj_data.verts, [], obj_data.faces)
            mesh.update()

            obj = bpy.data.objects.new(obj_data.skin_name, mesh)
            bpy.context.collection.objects.link(obj)
            obj.select_set(True)

            print(f"[LX] 导入成功!")
            self.report(
                {"INFO"}, f"成功导入: {obj_data.skin_name} ({len(obj_data.verts)} 顶点)"
            )
            return {"FINISHED"}

            bpy.ops.object.select_all(action="DESELECT")

            for obj_data in objects:
                if len(obj_data.verts) == 0:
                    continue

                if len(obj_data.faces) == 0:
                    continue

                mesh = bpy.data.meshes.new(obj_data.skin_name)
                mesh.from_pydata(obj_data.verts, [], obj_data.faces)
                mesh.update()

                obj = bpy.data.objects.new(obj_data.skin_name, mesh)
                bpy.context.collection.objects.link(obj)
                obj.select_set(True)

                if len(obj_data.uvs) > 0:
                    uv_layer = mesh.uv_layers.new(name="UV")
                    for poly in mesh.polygons:
                        for loop_index in poly.loop_indices:
                            vert_idx = mesh.loops[loop_index].vertex_index
                            if vert_idx < len(obj_data.uvs):
                                uv_layer.data[loop_index].uv = obj_data.uvs[vert_idx][
                                    :2
                                ]

            self.report({"INFO"}, f"成功导入 {len(objects)} 个模型对象")
            return {"FINISHED"}

        except Exception as e:
            import traceback

            print(f"导入SKC错误: {e}")
            traceback.print_exc()
            self.report({"ERROR"}, f"导入失败: {str(e)}")
            return {"CANCELLED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class GMC_OT_import(bpy.types.Operator):
    """导入流星GMB/GMC模型"""

    bl_idname = "lx.import_gmc"
    bl_label = "导入GMB/GMC模型"
    bl_options = {"PRESET"}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.gmb;*.gmc", options={"HIDDEN"})

    def execute(self, context):
        try:
            ext = os.path.splitext(self.filepath)[1].lower()

            if ext == ".gmb":
                from . import import_utils

                reader = import_utils.GMBReader(self.filepath)
                objects, materials, textures = reader.read_gmb()
            else:
                from . import import_utils

                reader = import_utils.GMCReader(self.filepath)
                objects, materials, textures = reader.read_gmc()

            bpy.ops.object.select_all(action="DESELECT")

            for obj_data in objects:
                if len(obj_data.verts) == 0:
                    continue

                mesh = bpy.data.meshes.new(obj_data.skin_name)
                mesh.from_pydata(obj_data.verts, [], obj_data.faces)
                mesh.update()

                obj = bpy.data.objects.new(obj_data.skin_name, mesh)
                bpy.context.collection.objects.link(obj)

            self.report({"INFO"}, f"成功导入 {len(objects)} 个模型对象")
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"导入失败: {str(e)}")
            return {"CANCELLED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class AMB_OT_import(bpy.types.Operator):
    """导入流星AMB动作文件"""

    bl_idname = "lx.import_amb"
    bl_label = "导入AMB动作"
    bl_options = {"PRESET"}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.amb", options={"HIDDEN"})

    def execute(self, context):
        try:
            from . import import_utils

            reader = import_utils.AMBReader(self.filepath)
            animations, bones, dummies = reader.read_amb()

            bpy.context.scene.frame_start = 0
            bpy.context.scene.frame_end = len(animations) - 1

            self.report({"INFO"}, f"成功导入AMB动作，共 {len(animations)} 帧")
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"导入失败: {str(e)}")
            return {"CANCELLED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class AMB_OT_export(bpy.types.Operator):
    """导出流星AMB动作文件"""

    bl_idname = "lx.export_amb"
    bl_label = "导出AMB动作"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.amb", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        try:
            from . import export_utils

            writer = export_utils.AMBWriter(self.filepath)
            self.report({"INFO"}, f"成功导出AMB动作文件")
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"导出失败: {str(e)}")
            return {"CANCELLED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class FMC_OT_export(bpy.types.Operator):
    """导出FMC动画文件"""

    bl_idname = "lx.export_fmc"
    bl_label = "导出FMC动画"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.fmc", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        try:
            from . import export_utils

            selected = context.selected_objects
            frame_start = context.scene.frame_start
            frame_end = context.scene.frame_end
            frame_count = frame_end - frame_start + 1

            writer = export_utils.FMCWriter(self.filepath)
            writer.write(selected, frame_count)

            pos_path = os.path.splitext(self.filepath)[0] + ".pos"
            pos_writer = export_utils.POSWriter(pos_path)
            pos_writer.write(frame_count)

            self.report({"INFO"}, f"成功导出FMC/POS动画文件")
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"导出失败: {str(e)}")
            return {"CANCELLED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class WP_OT_export(bpy.types.Operator):
    """导出WP路径点文件"""

    bl_idname = "lx.export_wp"
    bl_label = "导出WP路径点"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.wp", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        try:
            from . import export_utils

            selected = [
                obj
                for obj in context.selected_objects
                if obj.type == "EMPTY" or obj.type == "MESH"
            ]

            waypoints = []
            for i, obj in enumerate(selected):
                wp = {
                    "pos": [obj.location.x, obj.location.y, obj.location.z],
                    "size": 40,
                    "links": [],
                }

                for j, other in enumerate(selected):
                    if i != j:
                        dist = obj.location.distance_to(other.location)
                        flag = 0 if dist < 400 else 1
                        wp["links"].append({"index": j, "flag": flag, "dist": dist})

                waypoints.append(wp)

            writer = export_utils.WPWriter(self.filepath)
            writer.write(waypoints)

            self.report({"INFO"}, f"成功导出 {len(waypoints)} 个路径点")
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"导出失败: {str(e)}")
            return {"CANCELLED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class GMC_OT_export(bpy.types.Operator):
    """导出GMB模型文件"""

    bl_idname = "lx.export_gmb"
    bl_label = "导出GMB模型"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.gmb", options={"HIDDEN"})

    export_des: bpy.props.BoolProperty(name="同时导出DES文件", default=True)

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        try:
            from . import export_utils

            selected = [obj for obj in context.selected_objects if obj.type == "MESH"]

            if not selected:
                self.report({"ERROR"}, "没有选择可导出的模型对象")
                return {"CANCELLED"}

            materials = [
                {
                    "tex_id": 0,
                    "tex_type": "NORMAL",
                    "twoside": 0,
                    "blend": "DISABLE 1 0",
                    "opaque": 1.0,
                }
            ]
            textures = ["NONE"]

            writer = export_utils.GMBWriter(self.filepath)
            writer.write(selected, materials, textures)

            if self.export_des:
                des_path = os.path.splitext(self.filepath)[0] + ".des"
                des_writer = export_utils.DESWriter(des_path)
                des_writer.write(selected)

            self.report({"INFO"}, f"成功导出GMB/DES文件")
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"导出失败: {str(e)}")
            return {"CANCELLED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


classes = [
    SKC_OT_import,
    GMC_OT_import,
    AMB_OT_import,
    AMB_OT_export,
    FMC_OT_export,
    WP_OT_export,
    GMC_OT_export,
]
