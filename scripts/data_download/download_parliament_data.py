#!/usr/bin/env python3
"""
Download real data from Portuguese Parliament Open Data
"""

import requests
import os
import xml.etree.ElementTree as ET
from datetime import datetime

# Known XML endpoints for Portuguese Parliament data
XML_URLS = {
    'informacao_base_xvii': 'https://app.parlamento.pt/webutils/docs/doc.xml?path=6148523063446f764c324679626d56304c334e706447567a4c31684a566b786c5a79394551565276637955794d45466959334a70646e39446232317762334e705a47567a4c314e425543394a