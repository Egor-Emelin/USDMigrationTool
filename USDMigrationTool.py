import os
import hou


class USDTool:
    def __init__(self):
        self.asset_name = None

    def createTemplate(self, dirpath):
        # main function
        fbx_file = [file for file in os.listdir(dirpath) if file.endswith('.fbx')][0]
        self.asset_name = fbx_file[:-4]
        stage_path = '/stage'

        # SOP cleaning geo
        n_sopcreate = hou.node(stage_path).createNode('sopcreate', self.asset_name)
        n_sopcreate.parm('enable_partitionattribs').set(0)

        n_file = hou.node(n_sopcreate.path() + '/sopnet/create/').createNode('file')
        n_file.parm('file').set(dirpath + '/' + fbx_file)

        n_block_begin = n_file.createOutputNode('block_begin', 'foreach_begin1')
        n_block_begin.parm('method').set(1)
        n_block_begin.parm('blockpath').set('../foreach_end1')
        n_block_begin.parm('createmetablock').pressButton()

        n_metadata = hou.node(n_block_begin.parent().path() + '/foreach_begin1_metadata1')
        n_metadata.parm('method').set(2)
        n_metadata.parm('blockpath').set('../foreach_end1')

        n_attribwrangle = n_block_begin.createOutputNode('attribwrangle')
        n_attribwrangle.setInput(1, n_metadata)
        n_attribwrangle.parm('class').set(1)
        # n_attribwrangle.parm('snippet').set(
        #     'string assets[] = {"Body","Eye", "Glasses", "Hair", "Bottom", "Footwear", "Top", "Skin", '
        #     '"Teeth"};\ns@path = "/" + assets[detail(1,"iteration")];')
        n_attribwrangle.parm('snippet').set('string names = s@shop_materialpath;\nstring parts[] = split(names, '
                                            '"_");\nstring result = "";\nif (len(parts)>2) {\n    result = split(parts['
                                            '2], ".")[0];\n}\nelse{\n    result = split(parts[1], ".")[0];\n    '
                                            '}\ns@path = "/" + result;')

        n_block_end = n_attribwrangle.createOutputNode('block_end', 'foreach_end1')
        n_block_end.parm('itermethod').set(1)
        n_block_end.parm('method').set(1)
        n_block_end.parm('class').set(0)
        n_block_end.parm('useattrib').set(1)
        n_block_end.parm('attrib').set('shop_materialpath')
        n_block_end.parm('blockpath').set('../foreach_begin1')
        n_block_end.parm('templatepath').set('../foreach_begin1')

        n_attribdelete = n_block_end.createOutputNode('attribdelete')
        n_attribdelete.parm('ptdel').set('* ^P')
        n_attribdelete.parm('primdel').set('* ^path')

        n_output = n_attribdelete.createOutputNode('output')
        n_output.setGenericFlag(hou.nodeFlag.Display, True)
        n_output.setGenericFlag(hou.nodeFlag.Render, True)

        # proper naming structure
        n_primitive = hou.node(stage_path).createNode('primitive')
        n_primitive.parm('primpath').set(f'/{self.asset_name}')
        n_primitive.parm('primkind').set('component')

        n_graftstages = n_primitive.createOutputNode('graftstages')
        n_graftstages.parm('primkind').set('subcomponent')
        n_graftstages.setNextInput(n_sopcreate)

        # materials
        n_materiallibrary = n_graftstages.createOutputNode('materiallibrary')
        materials = ["Body", "Eye", "Glasses", "Hair", "Bottom", "Footwear", "Top", "Skin", "Teeth"]
        n_materiallibrary.parm('materials').set(len(materials))

        for i, material in enumerate(materials):
            n_materiallibrary.parm(f"matnode{i + 1}").set(material)
            n_materiallibrary.parm(f"matpath{i + 1}").set(f'/{self.asset_name}/materials/{material}_mat')
            n_materiallibrary.parm(f"assign{i + 1}").set(1)
            n_materiallibrary.parm(f"geopath{i + 1}").set(f'/{self.asset_name}/{self.asset_name}/{material}')

            n_subnet = n_materiallibrary.createNode('subnet', material)
            n_suboutput = hou.node(n_subnet.path() + '/suboutput1')
            n_mtlxstandard_surface = n_subnet.createNode('mtlxstandard_surface')
            mtlxstandard_surface_color_input = n_mtlxstandard_surface.inputIndex('base_color')
            mtlxstandard_surface_metalness_input = n_mtlxstandard_surface.inputIndex('metalness')
            mtlxstandard_surface_specular_roughness_input = n_mtlxstandard_surface.inputIndex('specular_roughness')
            mtlxstandard_surface_normal_input = n_mtlxstandard_surface.inputIndex('normal')
            mtlxstandard_surface_output = n_mtlxstandard_surface.outputIndex('out')

            # checks for diffuse, combined metal & roughness, normal maps
            conditions = []
            conditions2 = []
            conditions3 = []

            if material == 'Body':
                conditions = ["body", "-C"]

            elif material == 'Eye':
                conditions = ["eye", "-C"]

            elif material == 'Glasses':
                conditions = ["glasses", "-D"]
                conditions2 = ['glasses', '-M', '-R']

            elif material == 'Hair':
                conditions = ["hair", "-C"]
                conditions3 = ['hair', '-N']

            elif material == 'Bottom':
                conditions = ["pants", "-C"]
                conditions2 = ['pants', '-M', '-R']
                conditions3 = ['pants', '-N']

            elif material == 'Footwear':
                conditions = ["boots", "-C"]
                conditions2 = ['boots', '-M', '-R']
                conditions3 = ['boots', '-N']

            elif material == 'Top':
                conditions = ["jacket", "-C"]
                conditions2 = ['jacket', '-M', '-R']
                conditions3 = ['jacket', '-N']

            elif material == 'Skin':
                conditions = ["skin", "-C"]

            elif material == 'Teeth':
                conditions = ["teeth", "-C"]

            if len(conditions) > 0:
                base_color = [item for item in os.listdir(dirpath + '/Textures') if
                              all(cond in item for cond in conditions)][0]
                n_mtlximage = n_subnet.createNode('mtlximage')
                n_mtlximage.parm('file').set(dirpath + '\\Textures\\' + base_color)
                mtlximage_output = n_mtlximage.outputIndex('out')
                n_mtlxstandard_surface.setInput(mtlxstandard_surface_color_input, n_mtlximage, mtlximage_output)
            else:
                pass

            if len(conditions2) > 0:
                metal_roughness = [item for item in os.listdir(dirpath + '/Textures') if
                                   all(cond in item for cond in conditions2)][0]
                n_mtlximage_metalic_roughness = n_subnet.createNode('mtlximage')
                n_mtlximage_metalic_roughness.parm('file').set(dirpath + '\\Textures\\' + metal_roughness)
                n_mtlxseparate3c = n_mtlximage_metalic_roughness.createOutputNode('mtlxseparate3c')

                n_mtlxstandard_surface.setInput(mtlxstandard_surface_metalness_input, n_mtlxseparate3c,
                                                n_mtlxseparate3c.outputIndex('outr'))
                n_mtlxstandard_surface.setInput(mtlxstandard_surface_specular_roughness_input, n_mtlxseparate3c,
                                                n_mtlxseparate3c.outputIndex('outg'))
            else:
                pass

            if len(conditions3) > 0:
                normal = [item for item in os.listdir(dirpath + '/Textures') if
                          all(cond in item for cond in conditions3)][0]
                n_displacetexture = n_subnet.createNode('displacetexture')
                n_displacetexture.parm('texture').set(dirpath + '\\Textures\\' + normal)
                n_mtlxstandard_surface.setInput(mtlxstandard_surface_normal_input, n_displacetexture,
                                                n_displacetexture.outputIndex('outN'))
            else:
                pass

            n_suboutput.setNextInput(n_mtlxstandard_surface, mtlxstandard_surface_output)

            n_subnet.layoutChildren()
            n_subnet.setMaterialFlag(True)

        n_materiallibrary.layoutChildren()
        n_materiallibrary.setGenericFlag(hou.nodeFlag.Display, True)
        n_materiallibrary.setGenericFlag(hou.nodeFlag.Render, True)

        # exporting
        n_usd_rop = n_materiallibrary.createOutputNode('usd_rop')
        n_usd_rop.parm('lopoutput').set(dirpath + '/usd_export/' + self.asset_name + '.usd')
        n_usd_rop.parm('execute').pressButton()
        hou.node(stage_path).layoutChildren()
