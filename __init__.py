bl_info = {
    "name": "流星蝴蝶剑 Blender 工具箱",
    "author": "漠之北 (原版) / OpenCode (移植)",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > 流星蝴蝶剑",
    "description": "流星蝴蝶剑模型和动画导入导出工具集 - 支持SKC/BNC/GMB/GMC/AMB/FMC/POS/WP格式",
    "warning": "",
    "doc_url": "",
    "category": "Import-Export",
}

import bpy
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import operators
    from . import panels
    from . import import_utils
    from . import export_utils

classes = []


def register():
    from . import operators
    from . import panels
    from . import import_utils
    from . import export_utils

    for cls in operators.classes:
        bpy.utils.register_class(cls)

    for cls in panels.classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.lx_skc_path = bpy.props.StringProperty(
        name="SKC文件路径", default="", subtype="FILE_PATH"
    )
    bpy.types.Scene.lx_bnc_path = bpy.props.StringProperty(
        name="BNC骨骼路径", default="", subtype="FILE_PATH"
    )
    bpy.types.Scene.lx_gmb_path = bpy.props.StringProperty(
        name="GMB文件路径", default="", subtype="FILE_PATH"
    )
    bpy.types.Scene.lx_amb_path = bpy.props.StringProperty(
        name="AMB文件路径", default="", subtype="FILE_PATH"
    )
    bpy.types.Scene.lx_export_path = bpy.props.StringProperty(
        name="导出路径", default="", subtype="DIR_PATH"
    )

    bpy.ops.lx.import_skc
    bpy.ops.lx.import_gmc
    bpy.ops.lx.import_amb
    bpy.ops.lx.export_amb
    bpy.ops.lx.export_fmc
    bpy.ops.lx.export_wp
    bpy.ops.lx.export_gmb


def unregister():
    from . import operators
    from . import panels

    for cls in reversed(panels.classes):
        if hasattr(cls, "is_registered"):
            bpy.utils.unregister_class(cls)

    for cls in reversed(operators.classes):
        if hasattr(cls, "is_registered"):
            bpy.utils.unregister_class(cls)

    if hasattr(bpy.types.Scene, "lx_skc_path"):
        del bpy.types.Scene.lx_skc_path
    if hasattr(bpy.types.Scene, "lx_bnc_path"):
        del bpy.types.Scene.lx_bnc_path
    if hasattr(bpy.types.Scene, "lx_gmb_path"):
        del bpy.types.Scene.lx_gmb_path
    if hasattr(bpy.types.Scene, "lx_amb_path"):
        del bpy.types.Scene.lx_amb_path
    if hasattr(bpy.types.Scene, "lx_export_path"):
        del bpy.types.Scene.lx_export_path
