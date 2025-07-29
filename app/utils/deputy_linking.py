"""
Deputy Linking Utilities
========================

Reusable functions for linking deputies across legislaturas.
Currently uses name + birth date as unique key, but designed to be extensible.

TODO: Enhance with better unique identifiers when available
- Parliamentary ID numbers
- Citizen ID integration
- Photo matching
- More robust person identification
"""

def get_deputy_unique_key(nome_completo, data_nascimento=None):
    """
    Generate a unique key to identify the same person across legislaturas.
    
    Args:
        nome_completo (str): Full name of the deputy
        data_nascimento (str, optional): Birth date in YYYY-MM-DD format
    
    Returns:
        str: Unique key for grouping deputies
    """
    if not nome_completo:
        return None
    
    # Normalize name: strip whitespace, convert to lowercase for consistency
    normalized_name = nome_completo.strip().lower()
    
    if data_nascimento:
        # Use name + birth date as unique key (most reliable)
        return f"{normalized_name}|{data_nascimento}"
    else:
        # Fall back to name only (less reliable but necessary for incomplete data)
        return f"{normalized_name}|no_birthdate"

def group_deputies_by_person(deputies_list):
    """
    Group a list of deputy records by unique person.
    
    Args:
        deputies_list (list): List of deputy dictionaries with nome_completo, data_nascimento
    
    Returns:
        dict: Dictionary with unique_key -> list of deputy records
    """
    grouped = {}
    
    for deputy in deputies_list:
        unique_key = get_deputy_unique_key(
            deputy.get('nome_completo'),
            deputy.get('data_nascimento')
        )
        
        if unique_key:
            if unique_key not in grouped:
                grouped[unique_key] = []
            grouped[unique_key].append(deputy)
    
    return grouped

def get_most_recent_mandate(deputy_records):
    """
    Get the most recent mandate from a list of deputy records for the same person.
    
    Args:
        deputy_records (list): List of deputy records for the same person
    
    Returns:
        dict: Deputy record with the most recent mandate
    """
    if not deputy_records:
        return None
    
    # Sort by legislatura number (descending) to get most recent
    sorted_records = sorted(
        deputy_records,
        key=lambda x: x.get('legislatura_numero', 0),
        reverse=True
    )
    
    return sorted_records[0]

def enhance_deputy_with_career_info(deputy_record, all_records_for_person):
    """
    Enhance a deputy record with career information across all mandates.
    
    Args:
        deputy_record (dict): Main deputy record to enhance
        all_records_for_person (list): All records for this person
    
    Returns:
        dict: Enhanced deputy record with career statistics
    """
    enhanced = deputy_record.copy()
    
    # Calculate career statistics
    legislaturas_served = len(set(r.get('legislatura_numero') for r in all_records_for_person if r.get('legislatura_numero')))
    
    # Get all parties served with (for display)
    parties_served = list(set(
        f"{r.get('partido_sigla', 'N/A')}" 
        for r in all_records_for_person 
        if r.get('partido_sigla')
    ))
    
    # Get all circles represented
    circles_served = list(set(
        r.get('circulo', 'N/A') 
        for r in all_records_for_person 
        if r.get('circulo')
    ))
    
    # Determine if deputy is currently active
    has_active_mandate = any(
        record.get('legislatura_ativa') or record.get('mandato_ativo')
        for record in all_records_for_person
    )
    
    # Get the most recent completed mandate for inactive deputies
    latest_completed_mandate = None
    if not has_active_mandate:
        completed_mandates = [
            r for r in all_records_for_person 
            if r.get('mandato_fim') and not (r.get('legislatura_ativa') or r.get('mandato_ativo'))
        ]
        if completed_mandates:
            latest_completed = max(completed_mandates, 
                                 key=lambda x: x.get('legislatura_numero', 0))
            latest_completed_mandate = {
                'legislatura': latest_completed.get('legislatura_nome'),
                'periodo': f"{latest_completed.get('mandato_inicio', '')[:4]}-{latest_completed.get('mandato_fim', '')[:4]}" if latest_completed.get('mandato_inicio') and latest_completed.get('mandato_fim') else None
            }
    
    # Add career information
    enhanced['career_info'] = {
        'total_mandates': legislaturas_served,
        'parties_served': parties_served,
        'circles_served': circles_served,
        'first_mandate': min(r.get('legislatura_numero', float('inf')) for r in all_records_for_person),
        'latest_mandate': max(r.get('legislatura_numero', 0) for r in all_records_for_person),
        'is_multi_term': legislaturas_served > 1,
        'is_currently_active': has_active_mandate,
        'latest_completed_mandate': latest_completed_mandate
    }
    
    return enhanced