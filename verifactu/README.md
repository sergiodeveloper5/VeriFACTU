# Módulos Odoo 18 - Veri*FACTU

[![License AGPL-3](https://img.shields.io/badge/licence-AGPL--3-blue.svg)](http://www.gnu.org/licenses/agpl-3.0-standalone.html)

Colección de módulos para Odoo 18 que implementan la funcionalidad **Veri*FACTU** para el cumplimiento de las obligaciones fiscales españolas con la Agencia Estatal de Administración Tributaria (AEAT).

## 📦 Módulos Incluidos

### 🏛️ l10n_es_aeat_verifactu
**Comunicación Veri*FACTU** - Módulo principal para la comunicación con AEAT
- ✅ Versión: 18.0.1.0.0
- 🔧 Generación automática de códigos QR EPC
- 📄 Plantillas de factura mejoradas con integración Veri*FACTU
- ⚡ Sistema de cola asíncrona para envíos a AEAT
- 🔐 Gestión de certificados digitales

### 🏛️ l10n_es_aeat
**AEAT Base** - Módulo base para declaraciones AEAT
- ✅ Versión: 18.0.3.0.1
- 🔧 Funcionalidades base para comunicaciones con AEAT
- 📊 Gestión de agencias tributarias
- 🔐 Soporte para certificados digitales

### 📊 account_tax_balance
**Balance de Impuestos** - Gestión avanzada de balances fiscales
- ✅ Versión: 18.0.1.1.2
- 📈 Cálculos de balance de impuestos
- 📊 Reportes fiscales detallados

### 📅 date_range
**Rangos de Fechas** - Gestión de períodos temporales
- ✅ Versión: 18.0.1.0.9
- 📅 Definición de rangos de fechas personalizados
- 🔄 Generación automática de períodos
- 🔍 Filtros avanzados por rangos

## 🚀 Instalación

### Dependencias de Python
Antes de instalar los módulos, instala las dependencias de Python:

```bash
pip install -r requirements.txt
```