import discord
from discord.ext import commands
import json

# Définir les intentions du bot
intents = discord.Intents.all()
intents.members = True  # Activer l'accès aux informations sur les membres

# Créer un objet bot avec les intentions spécifiées
bot = commands.Bot(command_prefix='/', intents=intents)

def charger_notes():
    try:
        with open('notes.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Liste pour stocker les notes
notes = charger_notes()

def sauvegarder_notes():
    with open('notes.json', 'w') as json_file:
        json.dump(notes, json_file)

# Commande pour enregistrer une note avec le niveau
@bot.command(name='note')
async def note(ctx, profession, niveau):
    # Vérifiez si l'utilisateur a déjà des métiers enregistrés
    user_notes = next((user for user in notes if user['id'] == ctx.author.id), None)

    if user_notes:
        # Vérifiez si le métier est déjà enregistré pour l'utilisateur
        existing_metier = next((metier for metier in user_notes['metiers'] if metier['profession'].lower() == profession.lower()), None)

        if existing_metier:
            await ctx.send(f'Vous avez déjà enregistré le métier de {profession}. Utilisez /update {profession} <niveau> pour mettre à jour le niveau.')
        else:
            # Ajoutez le nouveau métier à la liste
            user_notes['metiers'].append({'profession': profession, 'niveau': niveau})
            sauvegarder_notes()
            await ctx.send(f'Vous avez été enregistré en tant que {profession} avec un niveau de {niveau}')
    else:
        # Si l'utilisateur n'a pas encore de métiers enregistrés, créez une nouvelle entrée
        notes.append({'id': ctx.author.id, 'nom_serveur': ctx.author.display_name, 'metiers': [{'profession': profession, 'niveau': niveau}]})
        sauvegarder_notes()
        await ctx.send(f'Vous avez été enregistré en tant que {profession} avec un niveau de {niveau}')


# Commande pour mettre à jour le niveau d'un métier
@bot.command(name='update')
async def update(ctx, profession, nouveau_niveau):
    # Vérifiez si l'utilisateur a déjà enregistré des métiers
    if ctx.author.id in notes:
        # Recherchez le métier dans la liste des métiers de l'utilisateur
        for metier in notes[ctx.author.id]['metiers']:
            if metier['profession'].lower() == profession.lower():
                # Mettez à jour le niveau du métier
                metier['niveau'] = nouveau_niveau
                sauvegarder_notes()
                await ctx.send(f'Votre niveau en tant que {profession} a été mis à jour à {nouveau_niveau}')
                return
    
    # Si l'utilisateur n'a pas encore enregistré le métier, informez-le
    await ctx.send(f'Vous n\'avez pas encore enregistré le métier de {profession}. Utilisez /note {profession} <niveau> pour l\'enregistrer.')

# Commande plus globale pour rechercher une note
@bot.command(name='search')
async def search(ctx, profession):
    # Créer un dictionnaire pour stocker les utilisateurs par niveau
    users_by_level = {}

    # Filtrer les utilisateurs par profession
    for user in notes:
        for metier in user.get('metiers', []):
            if isinstance(metier, dict) and metier.get('profession', '').lower() == profession.lower():
                niveau = metier.get('niveau', 'N/A')
                username = ctx.guild.get_member(user['id']).display_name.split(' ')[0]

                if niveau not in users_by_level:
                    users_by_level[niveau] = []

                users_by_level[niveau].append(username)

    # Construire le message de résultat
    results = []
    for niveau, usernames in users_by_level.items():
        users_str = ', '.join(usernames)
        results.append(f"{niveau} : {users_str}")

    if results:
        results_str = '\n'.join(results)
        await ctx.send(f'Niveaux {profession} :\n{results_str}')
    else:
        await ctx.send(f'Aucun utilisateur enregistré en tant que {profession}')




# Personnaliser la commande d'aide
@bot.command(name='aide')
async def help_command(ctx):
    embed = discord.Embed(title="Commandes disponibles", description="Voici les commandes disponibles :", color=0x00ff00)
    embed.add_field(name="/note", value="Enregistrer un métier avec un niveau. Exemple : /note Pêcheur 50", inline=False)
    embed.add_field(name="/update", value="Mettre à jour le niveau d'un métier. Exemple : /update Pêcheur 60", inline=False)
    embed.add_field(name="/search", value="Rechercher les utilisateurs enregistrés pour un métier. Exemple : /search Pêcheur", inline=False)
    embed.add_field(name="/notefor", value="Enregistrer un métier avec un niveau pour une personne autre que soit. Exemple : /notefor @Member Pêcheur 100", incline=False)
    await ctx.send(embed=embed)

# Commande pour noter un métier pour une personne
@bot.command(name='notefor')
async def notefor(ctx, member: discord.Member, profession, niveau):
    # Vérifiez si l'utilisateur a déjà des métiers enregistrés
    user_notes = next((user for user in notes if user['id'] == member.id), None)

    if user_notes:
        # Si l'utilisateur a déjà enregistré des métiers, ajoutez le nouveau métier à la liste
        user_notes['metiers'].append({'profession': profession, 'niveau': niveau})
    else:
        # Si l'utilisateur n'a pas encore de métiers enregistrés, créez une nouvelle entrée
        notes.append({'id': member.id, 'nom_serveur': member.display_name, 'metiers': [{'profession': profession, 'niveau': niveau}]})

    sauvegarder_notes()
    await ctx.send(f"Le métier {profession} pour {member.display_name} a été enregistré au niveau {niveau}")


@bot.command(name='delete')
async def delete(ctx, profession):
    # Charger les notes depuis le fichier
    global notes 
    notes = charger_notes()

    # Vérifiez si l'utilisateur a des métiers enregistrés
    user_id = ctx.author.id
    print(f"User ID: {user_id}")
    print(f"Notes: {notes}")

    user_data = next((entry for entry in notes if entry.get('id') == user_id), None)

    if user_data and 'metiers' in user_data:
        # Recherchez le métier dans la liste des métiers de l'utilisateur
        profession_lower = profession.lower()
        print(f"Avant suppression : {user_data['metiers']}")

        user_data['metiers'] = [metier for metier in user_data['metiers'] if metier['profession'].lower() != profession_lower]
        
        print(f"Après suppression : {user_data['metiers']}")
        sauvegarder_notes()
        
        if len(user_data['metiers']) > 0:
            # Si au moins un métier reste après la suppression
            await ctx.send(f'Le métier de {profession} a été supprimé de vos enregistrements.')
        else:
            # Si la liste des métiers est maintenant vide
            await ctx.send(f'Tous les métiers ont été supprimés. Utilisez /note {profession} <niveau> pour enregistrer un nouveau métier.')
    else:
        await ctx.send(f'Vous n\'avez pas encore enregistré de métiers. Utilisez /note {profession} <niveau> pour enregistrer un métier.')







# Lancer le bot
bot.run('MTE3NDA1ODI4NjY0ODEzNTcyMA.G-oErL.6cfkSMP2orFMoiwAqFacxgASnmmLCS52aceSWU')
