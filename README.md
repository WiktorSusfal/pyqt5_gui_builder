# pyqt5_dynamic_gui_builder
Solution to build PyQt5 QLayout object based on data from given XML config file


It is aimed to decouple the sets of instructions for building graphical UI and the rest of program code. User have to prepare XML document describing the desired PyQt5 layout and invoke relevant method in program which will return QLayout object. 

# Module developed
- PyQT5_GUI_Builder.py - main python file with definition of 'PyQT5_GUI_Builder' class. This is a kind of static class - the main method responsible for GUI building can be accessed by class name. In this file there is also a definition of 'MainWindow' class and some lines of executable code - for presentation purposes. 


# Features
So far the algorithm supports:
- QVBoxLayouts, QHBoxLayouts and QGridLayouts, 
- nested layouts objects - thank to recursion
- providing arguments for PyQt5 objects' constructors as variables that reference objects in existing application
- providing arguments' values as plain text in XML file

# Examples of use

1. Based on \Resources\Settings\EX1_QLabel_And_QLineEdit.xml config file - it contains definition of layout named "1_QLabel_1_QLineEdit". The result horizontal GUI layout consists of 1 QLabel and 1 QLineEdit edit in a single row. 
2. Based on \Resources\Settings\EX2_2_Rows_Of_QLabel_And_QLineEdit.xml - it contains definition of layout named "2_Rows_Of_QLabel_QLineEdit". The result vertical GUI layout consists of 2 nested horizontal layouts - each with its own QLabel and QLineEdit objects. 
