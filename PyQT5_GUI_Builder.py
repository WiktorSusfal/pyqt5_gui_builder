from PyQt5 import QtWidgets as QtWidgets
from importlib import *
from enum import *
import xml.etree.ElementTree as ET
import sys


class XmlNodeNames(Enum):
    """
    Enum class to store string names of particular xml nodes.
    """
    COMMON_DATA = 'common'
    MODULES_LIST = 'modules'
    CLASSES_LIST = 'classes'
    PARENT_LIST = 'parent_object_types'
    LAYOUTS_LIST = 'layouts'
    LAYOUT_NODE = 'layout'
    COMPONENTS_LIST = 'components'
    COMPONENT_NODE = 'component'
    CONSTRUCTOR_ARGS = 'constructor_args'
    FEATURES_LIST = 'features'
    FEATURE_PARAMS = 'feature_args'
    FEATURE_SETTING_ATTRS = 'setting_attributes'


class XmlAttrsNames(Enum):
    """
    Enum class to store string names of particular xml attributes.
    """
    MODULE_NAME = 'name'
    MODULE_ID = 'id'
    CLASS_NAME = 'name'
    CLASS_ID = 'id'
    PARENT_DESC = 'desc'
    PARENT_ID = 'id'
    LAYOUT_NAME = 'name'
    COMPONENT_TYPE = 'type'
    COMPONENT_CLASS_ID = 'class_id'
    COMPONENT_MODULE_ID = 'module_id'
    COMPONENT_ROW = 'row'
    COMPONENT_COLUMN = 'column'
    ARG_TYPE_ATTR = 'type'
    ARG_VALUE_ATTR = 'value'
    ARG_KIND_ATTR = 'kind'
    ARG_NAME_ATTR = 'arg_name'
    PARENT_TYPE_ID = 'parent_type_id'
    PARENT_MODULE_ID = 'module_id'
    SETTING_ATTR_NAME = 'name'


class XmlCommonAttrValues(Enum):
    """
    Enum class to store common values for particular xml attributes.
    """
    COMPONENT_TYPE_SELF = 'self'
    COMPONENT_TYPE_WIDGET = 'widget'
    ARG_TYPE_INTEGER = 'int'
    ARG_TYPE_STRING = 'str'
    ARG_TYPE_VARIABLE = 'var'
    ARG_KIND_NAMED = 'named'
    ARG_KIND_UNNAMED = 'unnamed'


class PyQT5_GUI_Builder:
    """
    Class to build PyQt5 layouts based on given XML config file. Such file should contain information about all GUI
    components - layouts and widgets. There is a support for multiple nested layouts and for binding particular widgets
    to functions.
    """

    @classmethod
    def returnGuiLayout(cls, config_filepath: str, layout_name: str, base_object) -> QtWidgets.QLayout:
        """
        Main class method that returns final QLayout object based on i.e. given XML config file.

        :param config_filepath: String path to XML config file.
        :param layout_name: Name of the desired layout described in the XML file (value of the 'name' attribute in
            the 'layout' XML node). There is a support for multiple layout definitions in one single file.
        :param base_object: Reference to the python object, that calls this function. If not used, pass 'None'.
        :return: QtWidgets.QLayout object with all the layouts and widgets described in XML config file.
        """
        config_tree = ET.parse(config_filepath)
        # Import all config settings that the file contains
        common_node = config_tree.find(XmlNodeNames.COMMON_DATA.value)

        # Return information about: modules and classes listed in XML config file
        modules_data = cls.returnValuePairsList(common_node,
                                                XmlNodeNames.MODULES_LIST.value,
                                                XmlAttrsNames.MODULE_ID.value,
                                                XmlAttrsNames.MODULE_NAME.value)
        classes_data = cls.returnValuePairsList(common_node,
                                                XmlNodeNames.CLASSES_LIST.value,
                                                XmlAttrsNames.CLASS_ID.value,
                                                XmlAttrsNames.CLASS_NAME.value)

        # Check if layout with given name exists in the xml config file
        layout_data = cls.returnLayoutNode(config_tree, layout_name)
        if layout_data is None:
            raise ValueError('Wrong layout name specified - such layout does not exists in ' + config_filepath)

        # Call the recursive function responsible for layout building
        gui_layout = cls.buildGuiLayout(layout_data, modules_data, classes_data, base_object)

        return gui_layout

    @staticmethod
    def returnValuePairsList(data_xml_node: ET.Element,
                             setting_list_node: str, data_id_attr: str, data_value_attr: str) -> dict:
        """
        Returns simple dictionary of key-value pairs based on given list of XML nodes. Key-value pairs are made based
        on given XML attributes' names - one for dictionary key and second for value.

        :param data_xml_node: xml.etree.ElementTree.Element object that contains lists of XML nodes.
        :param setting_list_node: String name of XML node that represents desired list of XML nodes.
        :param data_id_attr: String name of XML attribute that represents key for result dictionary.
        :param data_value_attr: String name of XML attribute that represents value for result dictionary.
        :return: Dictionary of simple key:value pairs.
        """
        data = dict()

        data_list = data_xml_node.find(setting_list_node)

        for piece_of_data in data_list:
            data_id = piece_of_data.attrib[data_id_attr]
            data_value = piece_of_data.attrib[data_value_attr]
            data[data_id] = data_value

        return data

    @staticmethod
    def returnLayoutNode(config_tree: ET.ElementTree, layout_name: str) -> ET.Element:
        """
        Returns 'layout' node (found at main level) from XML config file, that contains 'name' attribute with given
        value.

        :param config_tree: xml.etree.ElementTree object that represents whole XML tree read from XML file.
        :param layout_name: String value for 'name' attribute of 'layout' XML node to be found.
        :return: xml.etree.ElementTree.Element object describing desired layout (or None if no layout found).
        """
        layouts_node = config_tree.find(XmlNodeNames.LAYOUTS_LIST.value)
        lay_name_attr = XmlAttrsNames.LAYOUT_NAME.value

        for layout in layouts_node:
            if layout.attrib[lay_name_attr] == layout_name:
                return layout

        return None

    @classmethod
    def buildGuiLayout(cls, layout_node: ET.Element, modules_data: dict, classes_data: dict, base_object) \
            -> QtWidgets.QLayout:
        """
        Recursive class method responsible for building process of given PyQt5 layout.

        :param layout_node: xml.etree.ElementTree.Element object that represents XML node describing desired
            PyQt5 layout.
        :param modules_data: Dictionary of key-value pairs containing information about modules listed in XML file.
        :param classes_data: Dictionary of key-value pairs containing information about classes listed in XML file.
        :param base_object: Reference to the python object, that calls this function. If not used, pass 'None'.
        :return: QtWidgets.QLayout object with all component layouts and widgets - as described in XML file.
        """
        main_layout = None
        # Read the list of 'component' nodes under given 'layout' node
        layout_components = layout_node.find(XmlNodeNames.COMPONENTS_LIST.value)

        for component_node in layout_components:
            # Read the 'row' and 'column' attributes of given 'component' node - if they exist.
            # They exist if the 'component' node is under 'layout' node that represents QGridLayout object.
            placement_args = cls.returnComponentPlacementArgs(component_node)

            # If the next node that occurred is a 'component' node - build QWidget object based on it and add it to
            # existing layout.
            if component_node.tag == XmlNodeNames.COMPONENT_NODE.value:

                # Read the 'type' attribute of the current 'component' node. 'self' means, that this node represents
                # the constructor for main Layout object. 'widget' means that this node is for component QWidget object.
                component_type = component_node.attrib[XmlAttrsNames.COMPONENT_TYPE.value]
                # Build single component object (QWidget or main QLayout) based on the current XML node.
                component_object = cls.buildComponentObject(component_node, modules_data, classes_data, base_object)

                if component_type == XmlCommonAttrValues.COMPONENT_TYPE_SELF.value:
                    main_layout = component_object
                elif component_type == XmlCommonAttrValues.COMPONENT_TYPE_WIDGET.value:
                    main_layout.addWidget(component_object, *placement_args)

            # If the next node that occurred is a 'layout' node - call this function once again - to build
            # this component layout and add it to the existing layout.
            elif component_node.tag == XmlNodeNames.LAYOUT_NODE.value:
                main_layout.addLayout(cls.buildGuiLayout(component_node, modules_data, classes_data, base_object),
                                      *placement_args)

        return main_layout

    @staticmethod
    def returnComponentPlacementArgs(component_node: ET.Element):
        """
        Function to return array containing values of 'row' and 'column' attributes of 'component' or nested 'layout'
        nodes - if they exist. They exist if the parent layout object is a QGridLayout - they are needed to place the
        component inside QGridLayout object.

        :param component_node: xml.etree.ElementTree.Element object that represents current 'component' or
            nested 'layout' XML node
        :return: List containing 'row' and 'column' attrs' values - if they exist. If not - empty list.
        """
        placement_args = []
        if (XmlAttrsNames.COMPONENT_ROW.value in component_node.attrib and
                XmlAttrsNames.COMPONENT_COLUMN.value in component_node.attrib):
            placement_args.append(int(component_node.attrib[XmlAttrsNames.COMPONENT_ROW.value]))
            placement_args.append(int(component_node.attrib[XmlAttrsNames.COMPONENT_COLUMN.value]))

        return placement_args

    @classmethod
    def buildComponentObject(cls, component_node: ET.Element, modules_data: dict, classes_data: dict, base_object):
        """
        Method to build a single component of PyQt5 layout based on the given XML node object.

        :param component_node: xml.etree.ElementTree.Element object that represents 'component' XML node.
        :param modules_data: Dictionary of key-value pairs containing info about modules listed in XML config file
            ('module' nodes).
        :param classes_data: Dictionary of key-value pairs containing info about classes listed in XML config file
            ('class' nodes).
        :param base_object: Reference to python object that called this function (or acts like a host-object for result
            layout - e.g. contains methods that need to be connected to buttons etc...).
        :return: QWidget or QLayout object.
        """
        # Read:
        # - the name of the class that the result object should be an instance of,
        # - the name of the module that contains this class definition,
        # using the dictionaries of classes and modules and 'component' XML node attributes.
        class_name = classes_data[component_node.attrib[XmlAttrsNames.COMPONENT_CLASS_ID.value]]
        module_name = modules_data[component_node.attrib[XmlAttrsNames.COMPONENT_MODULE_ID.value]]

        # Return an object that represents desired class for current layout component.
        class_obj = cls.returnObjectByName(module_name, class_name)

        # Read constructor's arguments listed in current 'component' XML node.
        constructor_args, constructor_kwargs = cls.returnFunctionArguments(component_node,
                                                                           XmlNodeNames.CONSTRUCTOR_ARGS.value,
                                                                           modules_data,
                                                                           None,
                                                                           base_object)
        # Create result GUI component object from given class and constructor arguments.
        component_object = class_obj(*constructor_args, **constructor_kwargs)

        # Read list of 'feature' XML nodes for current PyQt5 GUI component. They represent various changes that can be
        # applied to the current GUI component after its creation - e.g. changing the size, connecting PyQt5 signals...
        component_features = component_node.find(XmlNodeNames.FEATURES_LIST.value)
        if component_features:
            # For every feature in the list - implement it
            for feature_node in component_features:
                component_object = cls.implementFeature(component_object, feature_node, modules_data, base_object)

        return component_object

    @staticmethod
    def returnObjectByName(module_name: str, object_name: str):
        """
        Returns object - e.g. class or function based on its name and the name of the module that contains relevant
        definition.

        :param module_name: String name of the module that contains definition of the object.
        :param object_name: String name of the desired object to be returned.
        :return: Any object - e.g. class or function
        """

        if module_name:
            # If given module is not imported already, import it.
            if module_name not in sys.modules:
                module = import_module(module_name)
            else:
                module = sys.modules[module_name]

            obj = getattr(module, object_name)
        else:
            # If module's name is not provided, try to find desired object in dictionary of global object in the current
            # module's scope.
            obj = globals()[object_name]

        return obj

    @classmethod
    def returnFunctionArguments(cls, component_node: ET.Element, args_node_name: str, modules_data: dict,
                                current_object, base_object) -> tuple:
        """
        Returns both: unnamed and named arguments for objects' constructors and methods based on 'arg' XML nodes
        placed in the config file.

        :param component_node: xml.etree.ElementTree.Element object that represents current 'component' XML node.
        :param args_node_name: String name of XML node that represents list of arguments ('arg' XML nodes).
        :param modules_data: Dictionary of key-value pairs containing info about modules listed in XML config file
            ('module' nodes).
        :param current_object: Object that was created based on the current 'component' XML node. If no object was
            created yet (this func is called for constructor's arguments), pass None.
        :param base_object: Reference to python object that called this function (or acts like a host-object for result
            layout - e.g. contains methods that need to be connected to buttons etc...).
        :return: Tuple - ( list of unnamed arguments, dictionary of named arguments )
        """

        result_args = list()
        result_kwargs = dict()
        args_list = component_node.find(args_node_name)

        if not args_list:
            return result_args, result_kwargs

        for arg in args_list:
            # Read following attributes for given 'arg' XML node:
            # - 'type' - describing type of data of the current argument
            # - 'value' - the main content of the current argument
            # - 'kind' - information whether the argument is 'named' or 'unnamed'
            arg_type = arg.attrib[XmlAttrsNames.ARG_TYPE_ATTR.value]
            arg_value = arg.attrib[XmlAttrsNames.ARG_VALUE_ATTR.value]
            arg_kind = arg.attrib[XmlAttrsNames.ARG_KIND_ATTR.value]

            # Cast arguments as desired datatypes.
            if arg_type == XmlCommonAttrValues.ARG_TYPE_INTEGER.value:
                arg_value = int(arg_value)
            elif arg_type in [XmlCommonAttrValues.ARG_TYPE_STRING.value, XmlCommonAttrValues.ARG_TYPE_VARIABLE.value]:
                arg_value = str(arg_value)

            # If the argument has "var" datatype specified, the 'value' contains the NAME of object/constant that
            # needs to be added to the result tuple. The function below is to get the actual reference of desired
            # object based on its parent's type.
            if arg_type == XmlCommonAttrValues.ARG_TYPE_VARIABLE.value:
                arg_value = cls.getObjectBasedOnParentType(arg, modules_data, arg_value, current_object, base_object)

            # Add this argument to relevant container based on its 'kind' XML attribute
            if arg_kind == XmlCommonAttrValues.ARG_KIND_NAMED.value:
                arg_name = arg.attrib[XmlAttrsNames.ARG_NAME_ATTR.value]
                result_kwargs[arg_name] = arg_value
            elif arg_kind == XmlCommonAttrValues.ARG_KIND_UNNAMED.value:
                result_args.append(arg_value)

        return result_args, result_kwargs

    @classmethod
    def getObjectBasedOnParentType(cls, xml_node: ET.Element, modules_data: dict, object_name: str, current_object,
                                   base_object):
        """
        Gets the reference of an object by given name and the type of object's parent - read from config XML file.

        :param xml_node: xml.etree.ElementTree.Element object that represents current XML node containing info about
            object to get.
        :param modules_data: Dictionary of key-value pairs containing info about modules listed in XML config file
            ('module' nodes).
        :param object_name: Name of the object which reference will be got.
        :param current_object: GUI object that was created based on the current 'component' XML node. If no object was
            created yet (this func is called for constructor's arguments), pass None.
        :param base_object: Reference to python object that called this function (or acts like a host-object for result
            layout - e.g. contains methods that need to be connected to buttons etc...).
        :return: Any object - reference got by name and object's parent type.
        """

        obj = None
        # In this case, there must be 'parent_type_id' attribute specified in given XML node. Read it. It stands for
        # the type of parent object that contains the object specified by name in the 'value' attribute in
        # 'arg' XML node.
        parent_type_id = xml_node.attrib[XmlAttrsNames.PARENT_TYPE_ID.value]

        # In the following case, the parent object of the one specified, is the current GUI component object
        # that is being created/modified.
        if parent_type_id == "0":
            # Assign the exact object to the result variable.
            obj = getattr(current_object, object_name)
        # In the following case, the parent object is a whole module.
        elif parent_type_id == "1":
            # In this case, there must be 'module_id' attribute specified for current XML node. Read it.
            # Read the module name using the id read from XML node and the dictionary of modules' information.
            module_name = modules_data[xml_node.attrib[XmlAttrsNames.PARENT_MODULE_ID.value]]
            # Assign the exact object to the result variable.
            obj = cls.returnObjectByName(module_name, object_name)
        # In the following case, the parent object is an object that called this function.
        elif parent_type_id == "2":
            # Assign the exact object to the result variable.
            obj = getattr(base_object, object_name)

        return obj

    @classmethod
    def implementFeature(cls, target_obj, feature_node: ET.Element, modules_data: dict, base_object):
        """
        Reads the information about desired modification that should be applied to current GUI component object and
        implements it. Information is read from 'feature' XML node in given config file.

        :param target_obj: Reference to the current GUI component that should be modified.
        :param feature_node: xml.etree.ElementTree.Element object that represents 'feature' XML node from config file.
        :param modules_data: Dictionary of key-value pairs containing info about modules listed in XML config file
            ('module' nodes).
        :param base_object: Reference to python object that called this function (or acts like a host-object for result
            layout - e.g. contains methods that need to be connected to buttons etc...).
        :return: Any object - current GUI component after modification.
        """

        # Read arguments of feature to be implemented (from 'arg' XML nodes listed inside 'feature' node)
        args, kwargs = cls.returnFunctionArguments(feature_node,
                                                   XmlNodeNames.FEATURE_PARAMS.value,
                                                   modules_data,
                                                   target_obj,
                                                   base_object)

        # Get the object (e.g. method) that is responsible for feature implementation. This object is described inside
        # 'setting_attributes' XML node, inside 'feature' node).
        setting_attr = cls.returnSettingAttribute(feature_node, modules_data, target_obj, base_object)

        # Do the modification of the current GUI object.
        setting_attr(*args, **kwargs)

        return target_obj

    @classmethod
    def returnSettingAttribute(cls, xml_node: ET.Element, modules_data, current_object, base_object):
        """
        Gets the method responsible for implementing particular feature based on the data placed under
        'feature' XML node in config file - inside 'setting_attributes' node.
 
        :param xml_node: xml.etree.ElementTree.Element object that represents 'feature' XML node from config file.
        :param modules_data: Dictionary of key-value pairs containing info about modules listed in XML config file
            ('module' nodes).
        :param current_object: Object that was created based on the current 'component' XML node.
        :param base_object: Reference to python object that called this function (or acts like a host-object for result
            layout - e.g. contains methods that need to be connected to buttons etc...).
        :return: Any object that represents e.g. method responsible for implementing given feature.
        """

        final_setting_attr = current_object
        # Sometimes there is a need to get the desired method "step-by-step". For example - for QPushButton, the method
        # responsible for setting 'clicked' action is 'QPushButton.clicked.connect', so there must be two
        # 'component_attr' XML nodes inside 'setting_attributes' node - first for 'clicked' property, and the second for
        # 'connect'.
        # This is why the following algorithm runs in a loop.
        component_setting_attrs = xml_node.find(XmlNodeNames.FEATURE_SETTING_ATTRS.value)
        for component_attr in component_setting_attrs:
            # Read the value of 'name' XML attribute for 'component_attr' node. This is a name of component
            # method/property responsible for feature implementation.
            attr_name = component_attr.attrib[XmlAttrsNames.SETTING_ATTR_NAME.value]

            # Get the reference of the object described by 'component_attr' node.
            final_setting_attr = cls.getObjectBasedOnParentType(component_attr, modules_data, attr_name,
                                                                final_setting_attr, base_object)

        return final_setting_attr


class MainWindow(QtWidgets.QMainWindow):
    """
    Sample class for presentation purposes. Contains attribute 'gui_layout' built by 'PyQT5_GUI_Builder.returnGuiLayout'
    function - based on given XML config file. This attribute (of QLayout type) is a main layout of the app window.
    """
    def __init__(self):
        super().__init__()
        # Build the main layout attribute based on given XML config file.
        self.gui_layout = PyQT5_GUI_Builder.returnGuiLayout('Resources/Settings/EX2_2_Rows_Of_QLabel_And_QLineEdit.xml',
                                                            '2_Rows_Of_QLabel_QLineEdit',
                                                            self)

        self.setWindowTitle('PyQt5 GUI Builder - from XML')
        self.setFixedSize(600, 400)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.lay = QtWidgets.QGridLayout(self.central_widget)
        self.lay.addLayout(self.gui_layout, 0, 0)

        self.show()

    @staticmethod
    def print_msg_method():
        """
        Test function to be connected to QPushButton generated automatically - based on XML config file.
            :return: None
        """
        print("Text comes from method")


def print_msg_function():
    """
    Test function to be connected to QPushButton generated automatically - based on XML config file.
        :return: None
    """
    print("Text comes from global function")


# Call the application
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    app_main_gui = MainWindow()
    app.exec_()
