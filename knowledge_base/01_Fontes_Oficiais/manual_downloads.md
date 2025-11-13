# Manual Download Guide for Portuguese Legal Documents

This guide provides step-by-step instructions for manually downloading
legal documents that cannot be accessed automatically due to website restrictions.

## Required Downloads

### 1. Código da Estrada (Consolidated Text)
- **URL**: https://diariodarepublica.pt/dr/detalhe/lei/72-2013-209000
- **Target Directory**: `01_Fontes_Oficiais/Diario_da_Republica/`
- **Filename**: `codigo_da_estrada_consolidado.pdf`

**Steps**:
1. Visit the URL above
2. Click "Download PDF" or similar button
3. Save to: `01_Fontes_Oficiais/Diario_da_Republica/codigo_da_estrada_consolidado.pdf`
4. Verify file size (should be > 1MB for complete document)

### 2. Decreto-Lei n.º 81/2006 (Parking Regulations)
- **Search URL**: https://dre.pt/
- **Search Terms**: "Decreto-Lei 81/2006"
- **Target Directory**: `01_Fontes_Oficiais/Diario_da_Republica/`
- **Filename**: `decreto_lei_81_2006.pdf`

**Steps**:
1. Go to https://dre.pt/
2. Search for "Decreto-Lei 81/2006"
3. Click on the official document
4. Download PDF version
5. Save to target directory

### 3. Lisbon Municipal Parking Regulations
- **URL**: https://lisboa.pt/
- **Search**: "Regulamento Geral de Estacionamento e Paragem na Via Pública"
- **Target Directory**: `01_Fontes_Oficiais/Lisboa_Municipal/`
- **Filename**: `lisboa_regulamento_estacionamento.pdf`

**Steps**:
1. Visit https://lisboa.pt/
2. Navigate to "Mobilidade" section
3. Find parking regulations
4. Download PDF
5. Save to target directory

### 4. Porto Municipal Parking Regulations
- **URL**: https://www.porto.pt/
- **Target Directory**: `01_Fontes_Oficiais/Porto_Municipal/`
- **Filename**: `porto_regulamento_estacionamento.pdf`

**Steps**:
1. Visit https://www.porto.pt/
2. Navigate to "Mobilidade e Transportes"
3. Find parking regulations
4. Download PDF
5. Save to target directory

## Access Issues and Solutions

### IMT (Instituto da Mobilidade e dos Transportes)
- **Issue**: Returns 403 Forbidden
- **Solution**: 
  - Use VPN with Portuguese IP
  - Access from within Portugal
  - Contact IMT directly for documents

### ANSR (Autoridade Nacional de Segurança Rodoviária)
- **Issue**: Website appears offline
- **Solution**:
  - Check if ANSR functions transferred to other agencies
  - Use Portal do Cidadão: https://www.portaldocidadao.pt/
  - Contact ACM (Autoridade da Concorrência e Regulação dos Serviços de Mercados)

## Automation Script

Run this script after downloading to verify files:
```python
python verify_manual_downloads.py
```

This will check if all files are present and valid.
