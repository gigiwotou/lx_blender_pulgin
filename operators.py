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
    import_armature: bpy.props.BoolProperty(
        name="导入骨骼", default=True, description="是否导入骨骼和权重"
    )
    bone_display_size: bpy.props.FloatProperty(
        name="骨骼显示大小",
        default=0.5,
        min=0.01,
        max=10.0,
        description="在视口中显示骨骼的大小",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "bnc_path")
        layout.prop(self, "import_armature")
        if self.import_armature:
            layout.prop(self, "bone_display_size")

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

            # 读取骨骼文件
            bones = []
            bone_count = 0
            dummey_count = 0

            # 确定BNC文件路径
            bnc_path = self.bnc_path
            print(f"[LX] 用户指定的BNC路径: '{bnc_path}'")

            if not bnc_path:
                # 自动查找同目录下的BNC文件
                skc_dir = os.path.dirname(skc_path)
                skc_name = os.path.splitext(os.path.basename(skc_path))[0]
                # 处理 p0_300.skc -> p0.bnc 的情况
                base_name = skc_name.split("_")[0]
                auto_bnc = os.path.join(skc_dir, base_name + ".bnc")
                print(f"[LX] 尝试查找BNC: {auto_bnc}")
                print(f"[LX] 文件是否存在: {os.path.exists(auto_bnc)}")
                if os.path.exists(auto_bnc):
                    bnc_path = auto_bnc
                    print(f"[LX] 自动找到BNC文件: {bnc_path}")
                else:
                    print(f"[LX] 未找到自动BNC文件")

            print(f"[LX] 最终BNC路径: '{bnc_path}'")
            if bnc_path:
                print(f"[LX] 文件是否存在检查: {os.path.exists(bnc_path)}")

            if bnc_path and os.path.exists(bnc_path):
                print(f"[LX] 读取骨骼文件: {bnc_path}")
                try:
                    bones, bone_count, dummey_count = import_utils.read_bnc(bnc_path)
                    print(f"[LX] 骨骼数量: {bone_count}, 虚拟体数量: {dummey_count}")
                    print(f"[LX] 实际读取骨骼数: {len(bones)}")
                    for i, b in enumerate(bones[:5]):
                        print(f"[LX] 骨骼[{i}]: {b.bone_name}, 父级: {b.parent_name}")
                except Exception as e:
                    print(f"[LX] 读取BNC出错: {e}")
                    import traceback

                    traceback.print_exc()
            else:
                print(f"[LX] 跳过骨骼读取 - 条件不满足")

            bpy.ops.object.select_all(action="DESELECT")

            # 存储导入的网格对象
            imported_objects = []

            for obj_data in objects:
                if len(obj_data.verts) == 0:
                    continue

                if len(obj_data.faces) == 0:
                    continue

                mesh = bpy.data.meshes.new(obj_data.skin_name)
                mesh.from_pydata(obj_data.verts, [], obj_data.faces)
                mesh.update()

                # 启用平滑着色
                for poly in mesh.polygons:
                    poly.use_smooth = True

                mesh.update()

                obj = bpy.data.objects.new(obj_data.skin_name, mesh)
                bpy.context.collection.objects.link(obj)
                obj.select_set(True)
                imported_objects.append((obj, obj_data))

                # 设置UV（修复：正确映射到面而不是顶点）
                if len(obj_data.uvs) > 0 and len(obj_data.faces) > 0:
                    uv_layer = mesh.uv_layers.new(name="UV")
                    # 遍历每个面，为每个面的顶点设置UV
                    for face_idx, face in enumerate(obj_data.faces):
                        if face_idx < len(mesh.polygons):
                            poly = mesh.polygons[face_idx]
                            for loop_i, loop_idx in enumerate(poly.loop_indices):
                                if loop_i < len(face):
                                    vert_idx = face[loop_i]
                                    if vert_idx < len(obj_data.uvs):
                                        uv = obj_data.uvs[vert_idx]
                                        uv_layer.data[loop_idx].uv = (uv[0], uv[1])

            # 创建骨骼和蒙皮
            print(
                f"[LX] 检查是否创建骨骼: import_armature={self.import_armature}, bones={len(bones)}, imported_objects={len(imported_objects)}"
            )
            if self.import_armature and bones and imported_objects:
                print("[LX] 条件满足，调用 create_armature_and_skin")
                self.create_armature_and_skin(
                    context, bones, imported_objects, self.bone_display_size
                )
            else:
                print(
                    f"[LX] 跳过骨骼创建: import_armature={self.import_armature}, bones={'有' if bones else '无'}, imported_objects={'有' if imported_objects else '无'}"
                )

            self.report({"INFO"}, f"成功导入 {len(objects)} 个模型对象")
            return {"FINISHED"}

        except Exception as e:
            import traceback

            print(f"导入SKC错误: {e}")
            traceback.print_exc()
            self.report({"ERROR"}, f"导入失败: {str(e)}")
            return {"CANCELLED"}

    def create_armature_and_skin(
        self, context, bones, imported_objects, bone_display_size=0.5
    ):
        """创建骨骼和蒙皮绑定 - 按3dsmax方式重构

        3dsmax的工作方式：
        1. 创建point对象（默认在原点）
        2. 设置parent关系
        3. 在父坐标系中(in coordsys parent)设置位置和旋转

        在Blender中模拟：
        1. 计算正确的世界坐标（父位置 + 父旋转 * 局部位置）
        2. 创建EditBone（不使用parent，避免Blender自动调整）
        3. 骨骼层级通过名称关系在逻辑上保持
        """
        import mathutils

        print("[LX] ==================== 开始创建骨骼 ====================")
        print(f"[LX] 传入骨骼数量: {len(bones)}")

        # 步骤1：按拓扑排序骨骼（父骨骼在前，子骨骼在后）
        print("[LX] 步骤1: 拓扑排序骨骼...")
        sorted_bones = []
        processed = set()

        def add_bone_and_children(bone_data):
            if bone_data.bone_name in processed:
                return
            processed.add(bone_data.bone_name)
            sorted_bones.append(bone_data)

            # 找到所有子骨骼
            for child in bones:
                if child.parent_name == bone_data.bone_name:
                    add_bone_and_children(child)

        # 从根骨骼开始
        for bone_data in bones:
            if not bone_data.parent_name or bone_data.parent_name == "NULL":
                add_bone_and_children(bone_data)

        # 添加剩余的（可能有parent但未找到）
        for bone_data in bones:
            if bone_data.bone_name not in processed:
                sorted_bones.append(bone_data)
                processed.add(bone_data.bone_name)

        print(f"[LX] 拓扑排序完成，共 {len(sorted_bones)} 块骨骼")

        # 步骤2：计算每个骨骼的世界变换矩阵
        print("[LX] 步骤2: 计算世界变换矩阵...")
        bone_world_matrix = {}  # 骨骼名称 -> 世界矩阵

        for bone_data in sorted_bones:
            bone_name = bone_data.bone_name

            # 局部变换
            local_pos = mathutils.Vector(bone_data.vpos)
            w, x, y, z = bone_data.vrot
            local_rot = mathutils.Quaternion((w, x, y, z))
            local_matrix = (
                mathutils.Matrix.Translation(local_pos) @ local_rot.to_matrix().to_4x4()
            )

            if bone_data.parent_name and bone_data.parent_name in bone_world_matrix:
                # 有父骨骼：世界矩阵 = 父矩阵 @ 局部矩阵
                parent_matrix = bone_world_matrix[bone_data.parent_name]
                world_matrix = parent_matrix @ local_matrix
            else:
                # 根骨骼：世界矩阵 = 局部矩阵
                world_matrix = local_matrix

            bone_world_matrix[bone_name] = world_matrix

            # 调试输出
            if bone_name in ["b", "d_wpnLP", "d_wpnL"]:
                world_pos = world_matrix.translation
                print(
                    f"[LX] {bone_name}: 局部{tuple(bone_data.vpos)} -> 世界{tuple(world_pos)}"
                )

        # 步骤3：创建Armature
        print("[LX] 步骤3: 创建Armature...")
        armature = bpy.data.armatures.new("Armature")
        armature.display_type = "OCTAHEDRAL"  # 使用八面体显示
        armature_obj = bpy.data.objects.new("Armature", armature)
        bpy.context.collection.objects.link(armature_obj)

        # 步骤4：进入编辑模式创建骨骼
        print("[LX] 步骤4: 创建EditBone...")
        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode="EDIT")

        edit_bones = armature.edit_bones
        bone_map = {}

        # 创建所有骨骼（使用世界坐标）
        for bone_data in sorted_bones:
            bone_name = bone_data.bone_name
            bone = edit_bones.new(bone_name)

            # 从世界矩阵提取位置和旋转
            world_matrix = bone_world_matrix[bone_name]
            world_pos = world_matrix.translation
            world_rot = world_matrix.to_quaternion()

            # 关键点：当前骨骼的pivot位置应该作为tail
            # head应该是父骨骼的pivot位置（如果是根骨骼则使用当前位置减去一定偏移）
            if bone_data.parent_name and bone_data.parent_name in bone_world_matrix:
                parent_matrix = bone_world_matrix[bone_data.parent_name]
                parent_pos = parent_matrix.translation
                bone.head = tuple(parent_pos)
                bone.tail = tuple(world_pos)
            else:
                # 根骨骼：head在当前位置，tail沿Z轴延伸
                bone.head = tuple(world_pos)
                direction = mathutils.Vector((0, 0, bone_display_size))
                direction.rotate(world_rot)
                tail_pos = world_pos + direction
                bone.tail = tuple(tail_pos)

            bone_map[bone_name] = bone

        # 步骤5：调整没有子骨骼的末端骨骼tail
        print("[LX] 步骤5: 调整末端骨骼tail...")
        for bone_data in sorted_bones:
            bone_name = bone_data.bone_name
            bone = bone_map[bone_name]

            # 查找子骨骼
            children = [b for b in sorted_bones if b.parent_name == bone_name]
            if not children:
                # 末端骨骼：沿当前骨骼方向延伸一定长度作为tail
                direction = mathutils.Vector(bone.tail) - mathutils.Vector(bone.head)
                if direction.length < 0.001:
                    # 如果head和tail几乎重合，使用旋转方向的Z轴
                    world_matrix = bone_world_matrix[bone_name]
                    world_rot = world_matrix.to_quaternion()
                    direction = mathutils.Vector((0, 0, bone_display_size))
                    direction.rotate(world_rot)
                else:
                    direction.normalize()
                    direction *= bone_display_size
                bone.tail = tuple(mathutils.Vector(bone.head) + direction)

        print("[LX] 步骤6: 完成，退出编辑模式...")
        bpy.ops.object.mode_set(mode="OBJECT")
        print(f"[LX] 骨骼创建完成: {len(bones)} 块骨骼")

        # 为每个网格对象添加蒙皮修改器
        print("[LX] 开始添加蒙皮...")
        print("[LX] 模型顶点位置范围:")
        for obj, obj_data in imported_objects:
            if obj_data.verts:
                xs = [v[0] for v in obj_data.verts]
                ys = [v[1] for v in obj_data.verts]
                zs = [v[2] for v in obj_data.verts]
                print(
                    f"[LX]   {obj.name}: X({min(xs):.2f}~{max(xs):.2f}), Y({min(ys):.2f}~{max(ys):.2f}), Z({min(zs):.2f}~{max(zs):.2f})"
                )
            print(f"[LX] 为 {obj.name} 添加蒙皮...")

            # 添加Armature修改器
            mod = obj.modifiers.new(name="Armature", type="ARMATURE")
            mod.object = armature_obj
            print(f"[LX] {obj.name} 添加Armature修改器完成")

            # 创建顶点组
            print(f"[LX] {obj.name} 创建顶点组...")
            for bone_data in bones:
                if bone_data.bone_name not in obj.vertex_groups:
                    obj.vertex_groups.new(name=bone_data.bone_name)
            print(f"[LX] {obj.name} 顶点组创建完成，共 {len(obj.vertex_groups)} 个")

            # 设置权重
            print(
                f"[LX] {obj.name} 检查权重数据: bone_ids长度={len(obj_data.bone_ids)}, 顶点数={len(obj_data.verts)}"
            )
            print(
                f"[LX] 可用骨骼: {[b.bone_name for b in bones[:5]]}... (共{len(bones)}个)"
            )

            if obj_data.bone_ids and len(obj_data.bone_ids) > 0:
                weight_count = 0
                error_count = 0

                # 打印前几个顶点的权重信息用于调试
                for vert_idx in range(min(3, len(obj_data.verts))):
                    if vert_idx < len(obj_data.bone_ids):
                        bone_ids = obj_data.bone_ids[vert_idx]
                        weights = obj_data.weight_array[vert_idx]
                        print(
                            f"[LX] 顶点{vert_idx}: 骨骼IDs={bone_ids}, 权重={weights}"
                        )

                for vert_idx in range(len(obj_data.verts)):
                    if vert_idx < len(obj_data.bone_ids):
                        bone_ids = obj_data.bone_ids[vert_idx]
                        weights = obj_data.weight_array[vert_idx]

                        for i, bone_id in enumerate(bone_ids):
                            if bone_id < len(bones) and i < len(weights):
                                bone_name = bones[bone_id].bone_name
                                weight = weights[i]
                                if weight > 0:
                                    try:
                                        vgroup = obj.vertex_groups[bone_name]
                                        vgroup.add([vert_idx], weight, "REPLACE")
                                        weight_count += 1
                                    except Exception as e:
                                        if error_count < 5:
                                            print(
                                                f"[LX] 权重设置错误: 顶点{vert_idx}, 骨骼'{bone_name}': {e}"
                                            )
                                        error_count += 1
                            else:
                                if error_count < 5:
                                    print(
                                        f"[LX] 骨骼ID越界: bone_id={bone_id}, 骨骼总数={len(bones)}"
                                    )
                                error_count += 1

                print(
                    f"[LX] {obj.name} 权重设置完成，共设置 {weight_count} 个权重, 错误: {error_count}"
                )
            else:
                print(f"[LX] {obj.name} 没有权重数据")

        print("[LX] ==================== 骨骼创建完成 ====================")

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
        print(f"[LX] 开始导入GMB/GMC: {self.filepath}")
        try:
            ext = os.path.splitext(self.filepath)[1].lower()

            if ext == ".gmb":
                from . import import_utils

                reader = import_utils.GMBReader(self.filepath)
                result = reader.read_gmb()
                print(f"[LX] GMB读取结果类型: {type(result)}")
                if isinstance(result, tuple) and len(result) == 3:
                    objects, materials, textures = result
                else:
                    objects = result
                    materials = []
                    textures = []
            else:
                from . import import_utils

                reader = import_utils.GMCReader(self.filepath)
                objects, materials, textures = reader.read_gmc()

            print(f"[LX] 对象数量: {len(objects)}")

            bpy.ops.object.select_all(action="DESELECT")

            for idx, obj_data in enumerate(objects):
                print(f"[LX] 处理对象 {idx}: {obj_data.skin_name}")
                print(
                    f"[LX]   verts: {len(obj_data.verts)}, faces: {len(obj_data.faces)}"
                )
                print(f"[LX]   faces类型: {type(obj_data.faces)}")
                if len(obj_data.faces) > 0:
                    print(f"[LX]   第一个面: {obj_data.faces[0]}")

                if len(obj_data.verts) == 0:
                    continue

                mesh = bpy.data.meshes.new(obj_data.skin_name)
                mesh.from_pydata(obj_data.verts, [], obj_data.faces)
                mesh.update()

                # 启用平滑着色
                for poly in mesh.polygons:
                    poly.use_smooth = True

                mesh.update()

                obj = bpy.data.objects.new(obj_data.skin_name, mesh)
                bpy.context.collection.objects.link(obj)

            self.report({"INFO"}, f"成功导入 {len(objects)} 个模型对象")
            return {"FINISHED"}

        except Exception as e:
            import traceback

            traceback.print_exc()
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
