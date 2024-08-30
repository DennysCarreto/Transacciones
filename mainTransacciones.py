import sys
import mysql.connector
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QSpacerItem, QSizePolicy,
                             QTableWidgetItem, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BASE DE DATOS DE CLIENTES")
        self.setGeometry(100, 100, 1050, 500)

        self.conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="admin",
            database="transaccionesht3"
        )
        self.cur = self.conn.cursor()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()
        
        # Sección izquierda
        left_layout = QGridLayout()
        left_layout.setVerticalSpacing(10)  # Espacio vertical entre filas
        
        # Labels y inputs
        labels = ["Nombre", "Apellido", "Dirección", "Teléfono"]
        self.inputs = {}

        ancho_fijo = 200
        for i, label_text in enumerate(labels):
            label = QLabel(label_text)
            self.inputs[label_text] = QLineEdit()
            self.inputs[label_text].setFixedWidth(ancho_fijo)
            
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            left_layout.addWidget(label, i, 0)
            left_layout.addWidget(self.inputs[label_text], i, 1)

        left_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum), 0, 2, 4, 1)
        
        # Botones
        button_layout = QHBoxLayout()
        buttons = ["START", "GUARDAR", "ROLL BACK", "COMMIT", "SALIR"]
        self.button_dict = {}
        for button_text in buttons:
            button = QPushButton(button_text)
            button.clicked.connect(getattr(self, f"on_{button_text.lower().replace(' ', '_')}"))
            button_layout.addWidget(button)
            self.button_dict[button_text] = button
        
        # Indicador de transacción
        self.transaction_indicator = QLabel("No hay transacción activa")
        self.transaction_indicator.setStyleSheet("background-color: red; color: white; padding: 5px;")
        
        left_widget = QWidget()
        left_main_layout = QVBoxLayout(left_widget)
        left_main_layout.addLayout(left_layout)
        left_main_layout.addLayout(button_layout)
        left_main_layout.addWidget(self.transaction_indicator)
        
        # Sección derecha (tabla)
        self.table = QTableWidget(0, 5)  # 5 columnas: ID + 4 campos del cliente
        self.table.setHorizontalHeaderLabels(["ID"] + labels)
        
        layout.addWidget(left_widget)
        layout.addWidget(self.table)
        
        central_widget.setLayout(layout)

        self.transaction_active = False
        self.update_button_states()
        self.load_data()

    def update_button_states(self):
        self.button_dict["START"].setEnabled(not self.transaction_active)
        self.button_dict["GUARDAR"].setEnabled(self.transaction_active)
        self.button_dict["ROLL BACK"].setEnabled(self.transaction_active)
        self.button_dict["COMMIT"].setEnabled(self.transaction_active)
        
        if self.transaction_active:
            self.transaction_indicator.setText("Transacción activa")
            self.transaction_indicator.setStyleSheet("background-color: green; color: white; padding: 5px;")
        else:
            self.transaction_indicator.setText("No hay transacción activa")
            self.transaction_indicator.setStyleSheet("background-color: red; color: white; padding: 5px;")

    def on_start(self):
        if not self.transaction_active:
            self.cur.execute("START TRANSACTION")
            self.transaction_active = True
            self.update_button_states()
            QMessageBox.information(self, "Transacción", "Transacción iniciada.")
        else:
            QMessageBox.warning(self, "Transacción", "Ya hay una transacción activa.")

    def on_roll_back(self):
        if self.transaction_active:
            self.conn.rollback()
            self.transaction_active = False
            self.update_button_states()
            QMessageBox.information(self, "Transacción", "Transacción revertida.")
            self.load_data()
        else:
            QMessageBox.warning(self, "Transacción", "No hay una transacción activa para revertir.")

    def on_commit(self):
        if self.transaction_active:
            self.conn.commit()
            self.transaction_active = False
            self.update_button_states()
            QMessageBox.information(self, "Transacción", "Transacción confirmada.")
            self.load_data()
        else:
            QMessageBox.warning(self, "Transacción", "No hay una transacción activa para confirmar.")

    def on_guardar(self):
        if not self.transaction_active:
            QMessageBox.warning(self, "Transacción", "Inicie una transacción antes de guardar.")
            return

        nombre = self.inputs['Nombre'].text()
        apellido = self.inputs['Apellido'].text()
        direccion = self.inputs['Dirección'].text()
        telefono = self.inputs['Teléfono'].text()

        try:
            # Modificamos esta consulta para no incluir el campo 'id'
            self.cur.execute('''INSERT INTO cliente (nombre, apellido, direccion)
                                VALUES (%s, %s, %s)''', (nombre, apellido, direccion))
            cliente_id = self.cur.lastrowid
            self.cur.execute('''INSERT INTO telefono (telefono, Cliente_id)
                                VALUES (%s, %s)''', (telefono, cliente_id))
            QMessageBox.information(self, "Guardar", "Datos guardados en la transacción.")
            self.load_data()
        except mysql.connector.Error as err:
            QMessageBox.warning(self, "Error", f"Error al guardar: {err}")

    def on_salir(self):
        if self.transaction_active:
            reply = QMessageBox.question(self, "Transacción activa", 
                                         "Hay una transacción activa. ¿Desea confirmarla antes de salir?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Yes:
                self.conn.commit()
            elif reply == QMessageBox.StandardButton.No:
                self.conn.rollback()
            else:
                return  # Cancel exit

        self.conn.close()
        self.close()

    def load_data(self):
        self.cur.execute('''SELECT cliente.id, cliente.nombre, cliente.apellido, 
                            cliente.direccion, telefono.telefono
                            FROM cliente
                            LEFT JOIN telefono ON cliente.id = telefono.Cliente_id''')
        data = self.cur.fetchall()
        self.table.setRowCount(0)
        for row_number, row_data in enumerate(data):
            self.table.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.table.setItem(row_number, column_number, QTableWidgetItem(str(data)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())