import bpy


class LX_PT_main(bpy.types.Panel):
    """流星蝴蝶剑工具箱主面板"""

    bl_label = "流星蝴蝶剑 工具箱"
    bl_idname = "LX_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "流星蝴蝶剑"

    def draw(self, context):
        layout = self.layout

        layout.label(text="流星蝴蝶剑 Blender 辅助工具")
        layout.separator()

        col = layout.column(align=True)
        col.operator("lx.import_skc", icon="IMPORT")
        col.operator("lx.import_gmc", icon="IMPORT")
        col.operator("lx.import_amb", icon="IMPORT")

        layout.separator()

        col = layout.column(align=True)
        col.operator("lx.export_amb", icon="EXPORT")
        col.operator("lx.export_fmc", icon="EXPORT")
        col.operator("lx.export_wp", icon="EXPORT")
        col.operator("lx.export_gmb", icon="EXPORT")

        layout.separator()

        box = layout.box()
        box.label(text="使用说明:")
        box.label(text="• SKC导入需要配套BNC骨骼文件")
        box.label(text="• GMB/GMC支持模型和动画导入")
        box.label(text="• AMB支持动作导入导出")
        box.label(text="• FMC/POS用于道具动画导出")
        box.label(text="• WP用于路径点导出")


class LX_PT_import(bpy.types.Panel):
    """导入面板"""

    bl_label = "模型导入"
    bl_idname = "LX_PT_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "流星蝴蝶剑"
    bl_parent_id = "LX_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="SKC人物模型:")
        row = box.row()
        row.operator("lx.import_skc", text="选择SKC文件")

        box = layout.box()
        box.label(text="GMB/GMC模型:")
        row = box.row()
        row.operator("lx.import_gmc", text="选择GMB/GMC文件")

        box = layout.box()
        box.label(text="AMB动作:")
        row = box.row()
        row.operator("lx.import_amb", text="选择AMB文件")


class LX_PT_export(bpy.types.Panel):
    """导出面板"""

    bl_label = "模型导出"
    bl_idname = "LX_PT_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "流星蝴蝶剑"
    bl_parent_id = "LX_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="GMB模型导出:")
        row = box.row()
        row.operator("lx.export_gmb", text="导出GMB模型")

        box = layout.box()
        box.label(text="DES场景文件:")
        box.label(text="(随GMB导出自动生成)")

        box = layout.box()
        box.label(text="COB碰撞文件:")
        row = box.row()
        row.operator("lx.export_gmb", text="导出COB碰撞")


class LX_PT_animation(bpy.types.Panel):
    """动画导出面板"""

    bl_label = "动画导出"
    bl_idname = "LX_PT_animation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "流星蝴蝶剑"
    bl_parent_id = "LX_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="FMC动画 (道具/武器):")
        row = box.row()
        row.operator("lx.export_fmc", text="导出FMC动画")

        box = layout.box()
        box.label(text="POS姿态文件:")
        box.label(text="(随FMC导出自动生成)")

        box = layout.box()
        box.label(text="AMB动作 (人物):")
        row = box.row()
        row.operator("lx.export_amb", text="导出AMB动作")

        box = layout.box()
        box.label(text="WP路径点:")
        row = box.row()
        row.operator("lx.export_wp", text="导出路径点")


class LX_PT_tools(bpy.types.Panel):
    """辅助工具面板"""

    bl_label = "辅助工具"
    bl_idname = "LX_PT_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "流星蝴蝶剑"
    bl_parent_id = "LX_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="骨骼工具:")
        box.label(text="• 骨骼绑定支持")
        box.label(text="• 权重自动分配")

        box = layout.box()
        box.label(text="特效轨迹:")
        box.label(text="• TRC轨迹导出")

        box = layout.box()
        box.label(text="MC菜单:")
        box.label(text="• MC文件导出")


classes = [
    LX_PT_main,
    LX_PT_import,
    LX_PT_export,
    LX_PT_animation,
    LX_PT_tools,
]
