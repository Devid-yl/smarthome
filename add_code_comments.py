#!/usr/bin/env python3
"""
Script pour ajouter des commentaires DATABASE QUERY et WEBSOCKET BROADCAST
dans tous les handlers pour faciliter la navigation dans le code.
"""

from pathlib import Path


def add_database_comments(content):
    """Ajoute les commentaires DATABASE QUERY avant async with async_session_maker()."""
    
    # Pattern pour trouver les occurrences de async with async_session_maker
    # Ajouter un commentaire descriptif si pas déjà présent
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        # Vérifier si la ligne précédente contient déjà un commentaire DATABASE QUERY
        has_comment = False
        if i > 0:
            prev_line = lines[i-1].strip()
            if 'DATABASE QUERY' in prev_line:
                has_comment = True
        
        # Si c'est une ligne avec async_session_maker et pas déjà commentée
        if 'async with async_session_maker()' in line and not has_comment:
            indent = len(line) - len(line.lstrip())
            comment = ' ' * indent + '# DATABASE QUERY: Opération sur la base de données'
            new_lines.append(comment)
        
        new_lines.append(line)
    
    return '\n'.join(new_lines)


def add_websocket_comments(content):
    """Ajoute les commentaires WEBSOCKET BROADCAST avant les appels broadcast."""
    
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        # Vérifier si la ligne précédente contient déjà un commentaire WEBSOCKET
        has_comment = False
        if i > 0:
            prev_line = lines[i-1].strip()
            if 'WEBSOCKET BROADCAST' in prev_line or 'WEBSOCKET' in prev_line:
                has_comment = True
        
        # Si c'est une ligne avec broadcast et pas déjà commentée
        if ('broadcast_' in line or 'RealtimeHandler.broadcast' in line) and not has_comment:
            # Ne pas commenter les définitions de fonctions
            if 'def broadcast' not in line and 'async def' not in line:
                indent = len(line) - len(line.lstrip())
                comment = ' ' * indent + '# WEBSOCKET BROADCAST: Diffusion temps réel aux clients WebSocket'
                new_lines.append(comment)
        
        new_lines.append(line)
    
    return '\n'.join(new_lines)


def process_file(filepath):
    """Traite un fichier pour ajouter les commentaires."""
    print(f"Traitement de {filepath.name}...")
    
    content = filepath.read_text(encoding='utf-8')
    original_content = content
    
    # Ajouter les commentaires
    content = add_database_comments(content)
    content = add_websocket_comments(content)
    
    # Sauvegarder si modifié
    if content != original_content:
        filepath.write_text(content, encoding='utf-8')
        print(f"  ✓ {filepath.name} modifié")
        return True
    else:
        print(f"  ⊙ {filepath.name} inchangé")
        return False


def main():
    """Point d'entrée principal."""
    # Chemin vers le dossier handlers
    base_path = Path(__file__).parent / 'smarthome' / 'tornado_app' / 'handlers'
    
    if not base_path.exists():
        print(f"❌ Dossier introuvable: {base_path}")
        return
    
    # Liste des fichiers à traiter
    files_to_process = [
        'users_api.py',
        'automation.py',
        'automation_rules.py',
        'house_members.py',
        'event_history.py',
        'user_positions.py',
        'websocket.py',
        'weather.py',
        'grid_editor.py',
    ]
    
    modified_count = 0
    
    for filename in files_to_process:
        filepath = base_path / filename
        if filepath.exists():
            if process_file(filepath):
                modified_count += 1
        else:
            print(f"⚠️  Fichier non trouvé: {filename}")
    
    print(f"\n✅ Terminé! {modified_count} fichier(s) modifié(s)")


if __name__ == '__main__':
    main()
