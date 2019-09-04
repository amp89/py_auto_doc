import scandir
import sys
import os
import re
DEP_RE = re.compile(r"(\s*\.*)(\w+\()")
'''
run from root dir of project
'''
EXCLUDE_DIR = ["venv", ".ipynb_checkpoints","ipynb"]
EXCLUDE_FILE = ["__init__", "auto_doc"]
EXCLUDE_DEPS = ["print","list","enumerate","Exception"]
EXCLUDE_ARG = ["self"]

def get_annotation_list(line_list, idx):
    annotation_list = []
    if line_list[idx-1].strip().startswith("@"):
        annotation_list.append(line_list[idx-1].strip())
        annotation_list = annotation_list + get_annotation_list(line_list, idx-1)
    
    return annotation_list
                
def get_f_args(line):
    try:
        arg_csv = line.split("(")[1].split(")")[0]
    except IndexError:
        return []
    arg_list = [a.strip() for a in arg_csv.split(",") if a != ""]
    arg_list = [a for a in arg_list if a not in EXCLUDE_ARG]
    return arg_list

def get_thingy(type_of_thingy, line_list, idx, pause_characters=False):
#     print(f"{idx}|{pause_characters}|{line_list[idx]}")
    
    return_list = []
    if pause_characters == True and ("'''" in line_list[idx] or  '"""' in line_list[idx]):
        if idx+1 < len(line_list):
            return_list = get_thingy(type_of_thingy, line_list, idx+1, pause_characters=False)
    elif pause_characters == True and not ("'''" in line_list[idx] or  '"""' in line_list[idx]):
        if idx+1 < len(line_list):
            return_list = get_thingy(type_of_thingy, line_list, idx+1, pause_characters=pause_characters)
        
    elif pause_characters == False and ("'''" in line_list[idx] or  '"""' in line_list[idx]):
        if idx+1 < len(line_list):
            return_list = get_thingy(type_of_thingy, line_list, idx+1, pause_characters=True)
    else:

        if line_list[idx].startswith(" ") and line_list[idx].strip().split(" ")[0] == str(type_of_thingy):
            try:
                return_list.append(line_list[idx].strip().split("{} ".format(str(type_of_thingy)))[1])
            except IndexError:
                pass
        if idx + 1 < len(line_list)\
                  and not line_list[idx+1].strip().startswith("class") \
                  and not line_list[idx+1].strip().startswith("def"):
            return_list = return_list + get_thingy(type_of_thingy, line_list, idx+1)
    return return_list

def get_attributes(line_list, idx):
    
    attr_list = []
    if " self." in line_list[idx] or ",self." in line_list[idx]:
        attr_list = [element for element in line_list[idx].split(" ") if element.strip().startswith("self.")]
        attr_list = [element.split("=")[0].strip() for element in attr_list]
        mstr_attr_list = []
        for attr_l in attr_list:
            mstr_attr_list += [element.strip() for element in attr_l.split(",")]
        attr_list = [element for element in attr_list if not element.strip().endswith(")")]
    if idx + 1 < len(line_list) \
              and not line_list[idx+1].strip().startswith("class"):
        attr_list = attr_list + get_attributes(line_list, idx+1)
    attr_list = [x for x in attr_list if "(" not in x]
    return attr_list

def get_deps(line_list, idx):
    return None
    return_list = []
    if not line_list[idx].strip().startswith("def") and not line_list[idx].strip().startswith("class") \
            and ")" in line_list[idx].split("#")[0].strip() and "(" in line_list[idx].split("#")[0].strip():
        re_matches = re.findall(string=line_list[idx].split("#")[0].strip(), pattern=DEP_RE)
        return_list = [thing[1].strip("(").strip(".").strip() for thing in re_matches]
    if idx + 1 < len(line_list) and line_list[idx+1].startswith(" ") \
          and not line_list[idx+1].strip().startswith("class") \
          and not line_list[idx+1].strip().startswith("def"):
        return_list = return_list + get_deps(line_list, idx+1)
    return_list = [x for x in return_list if x not in EXCLUDE_DEPS]
    return_list = list(set(return_list))
    return return_list
    
def get_import_list(line_list):
    imports = []
    for line in line_list:
        if line.startswith('import'):
            import_list = line.replace("import","").strip().split(",")
            import_list = [x.strip() for x in import_list]
            imports += import_list
        elif (line.startswith('from') and 'import' in line):
            import_list = line.replace("from","").strip().split("import")[-1].split(",")
            first_part = line.replace("from","").strip().split("import")[0]
            import_list = [first_part + x.strip() for x in import_list]
            import_list = [x.replace(" ",".").replace(":","") for x in import_list]
            imports += import_list
    return imports

def write_lines(file_obj, header, iter_list):
    if iter_list:
        sys.stdout.write("\n\n##### {}".format(str(header)))
        file_obj.write("\n\n##### {}".format(str(header)))
        for i in iter_list:
            this_line = "\n- {}".format(str(i))
            sys.stdout.write(this_line)
            file_obj.write(this_line)

def write_data(file_obj, current_module=None, dep_list=None, annotation_list=None, current_class=None,\
                        inheritance_list=None, attribute_list=None, current_function=None,
                        args_list=None, return_list=None, exception_list=None):

    full_module_parts_list = list(filter(lambda x: x, [current_module,current_class,current_function]))
    full_module_str = ".".join(full_module_parts_list)
    full_module_str = "\n\n#### {}".format(str(full_module_str))

    sys.stdout.write(full_module_str)
    file_obj.write(full_module_str)
    
    write_lines(file_obj, header="Inherits from", iter_list=inheritance_list)
    write_lines(file_obj, header="Attributes", iter_list=attribute_list)
    write_lines(file_obj, header="Dependencies", iter_list=dep_list)
    
    write_lines(file_obj, header="Arguments", iter_list=args_list)
    write_lines(file_obj, header="Returns", iter_list=return_list)
    write_lines(file_obj, header="Exceptions", iter_list=exception_list)
    write_lines(file_obj, header="Annotations", iter_list=annotation_list)

    
    
    
    sys.stdout.flush()
    
def write_import_list(file_obj, import_list):
    write_lines(file_obj, header="Imports", iter_list=import_list)

def document_module(module_path, file_obj):
    module_name = module_path.rstrip(".py").replace("./","").replace(".","").replace("\\",".").replace("/",".").lstrip(".")
    
    file_obj.write("\n\n# {}\n".format(str(module_name)))
    sys.stdout.write("\n\n# {}\n".format(str(module_name)))
    with open(module_path, "r") as f:
        current_class = None
        current_function = None
        current_module = module_name
        line_list = f.readlines()
        line_list = [element for element in line_list if not element.strip().startswith("#")]
        
        import_list = get_import_list(line_list)
        write_import_list(file_obj, import_list)
        
        for idx, line in enumerate(line_list):
            line = line.replace("\n","")
            if line.strip() == "":
                continue     
                
            #determine current class:
            if line.startswith("class"):
                current_class = line.split("class ")[1].split("(")[0]
                inheritance_list = get_f_args(line)
                attribute_list = get_attributes(line_list, idx)
                write_data(file_obj, current_module=current_module, dep_list=None, annotation_list=None, current_class=current_class,\
                        inheritance_list=inheritance_list, attribute_list=attribute_list, current_function=None,
                        args_list=None, return_list=None, exception_list=None)
            else:
                inheritance_list = None
                attribute_list = None
                
            #determine class inheritance
            
            #determine current function (and if function is part of a class)
            if line.startswith("def"):
                current_class = None
                current_function = line.split("def ")[1].split("(")[0]
                args_list = get_f_args(line)
                return_list = get_thingy("return", line_list, idx)
                exception_list = get_thingy("raise", line_list, idx)
                annotation_list = get_annotation_list(line_list, idx)
                #dep_list = get_deps(line_list, idx)
                dep_list = None
                write_data(file_obj, current_module, dep_list, annotation_list, current_class, inheritance_list, attribute_list, current_function, args_list, return_list, exception_list)
              
            elif line.startswith(" ") and "def " in line:
                current_function = line.split("def ")[1].split("(")[0]
                args_list = get_f_args(line)
                return_list = get_thingy("return", line_list, idx)
                exception_list = get_thingy("raise", line_list, idx)
                annotation_list = get_annotation_list(line_list, idx)
                #dep_list = get_deps(line_list, idx)
                dep_list = None
                write_data(file_obj, current_module, dep_list, annotation_list, current_class, inheritance_list, attribute_list, current_function, args_list, return_list, exception_list)
              

            
            

def scany_stuff(scan_path, file_obj):
    for element in scandir.scandir(scan_path):
        if element.is_dir():
            matches = list(filter(lambda x: x in element.path, EXCLUDE_DIR))
            if not matches:
                scany_stuff(element.path, file_obj)
        elif element.is_file():
            if element.name.endswith(".py") and element.name.split(".")[0] not in EXCLUDE_FILE:
                document_module(element.path, file_obj)
            
if __name__=="__main__":
    with open("text.md","w") as file_obj:
        scany_stuff(os.curdir,file_obj=file_obj)
