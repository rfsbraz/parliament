# Portuguese Parliament Field Translators

This directory contains thematic field translation modules for Portuguese Parliament data, organized by functional area.

## Module Organization

### `publications.py`
- **TipodePublicacao** enum with 21 publication type codes
- Used across models: IntervencaoParlamentar, IniciativaPublicacao, RequerimentoPublicacao
- Translates codes like "A" → "DAR II série A"

### `deputy_activities.py` 
- **TipodeAtividade** enum with 24 activity type codes
- **TipodeRequerimento** enum with 5 request type codes
- **Committee status** translations (suplente/efetivo)
- **Delegation types** (Nacional/Internacional)
- Used across models: ActividadesParlamentaresOut, ActividadesComissaoOut, RequerimentosOut

### `initiatives.py`
- **TipodeIniciativa** enum with 11 initiative type codes  
- **Initiative phases** for parliamentary procedure stages
- Used across models: IniciativasOut, IniciativaParlamentar

### `parliamentary_interventions.py`
- **Intervention types** for parliamentary debates
- **Publication supplements** and Assembly Diary formatting
- Combines intervention-specific logic with shared publication types
- Used across models: IntervencaoParlamentar, IntervencaoPublicacao

## Usage Patterns

### Individual Model Translation
```python
from database.translators.deputy_activities import deputy_activity_translator

# In your application/API layer
activity = session.query(ActividadesParlamentaresOut).first()
readable_type = deputy_activity_translator.activity_type(activity.act_tp)
```

### API Response Formatting
```python
from database.translators.publications import publication_translator

intervention = session.query(IntervencaoParlamentar).first()
api_response = {
    "id": intervention.id,
    "publication_type": {
        "code": intervention.pub_tp,
        "description": publication_translator.publication_type(intervention.pub_tp)
    }
}
```

### Validation Workflows
```python
from database.translators.initiatives import initiative_translator

translation = initiative_translator.get_initiative_type("J")
if translation.is_valid:
    print(f"Valid initiative: {translation.description}")
else:
    print(f"Invalid code: {translation.code}")
```

## Design Principles

1. **Thematic Organization**: Each module focuses on a specific functional area
2. **Enum-Based Safety**: All translations use Python enums for type safety
3. **Official Documentation**: All mappings based on December 2017 Parliament docs
4. **Separation of Concerns**: Translation logic separated from data processing
5. **Shared Components**: Common functionality (like publications) reused across modules
6. **Validation Support**: All translators provide validity checks for codes

## Cross-References

### Database Models → Translator Mapping

| Model | Field | Translator Module | Method |
|-------|-------|------------------|---------|
| IntervencaoParlamentar | pub_tp | publications | publication_type() |
| ActividadesParlamentaresOut | act_tp | deputy_activities | activity_type() |
| IniciativasOut | ini_tp | initiatives | initiative_type() |
| RequerimentosOut | req_tp | deputy_activities | request_type() |
| ComissoesOut | cms_situacao | deputy_activities | committee_status() |

### Official Documentation Mapping

All translations are based on:
- **Source**: "Significado das Tags do Ficheiro AtividadeDeputado<Legislatura>.xml"
- **Date**: December 2017
- **Validation**: Consistent across Constituinte through X Legislatures
- **Location**: `E:\dev\parliament\scripts\data_processing\data\downloads\atividade_Deputado\`