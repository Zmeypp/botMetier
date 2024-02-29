import mysql.connector
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os

load_dotenv()

bot_token = os.getenv("TOKEN")
db_user = os.getenv("DATABASE_USERNAME")
db_pass = os.getenv("DATABASE_PASSWORD")
db_host = os.getenv("DATABASE_HOST")
db_name = os.getenv("DATABASE_NAME")

intents = discord.Intents.all()
intents.members = True # Activer l'accès aux informations sur les membres

bot = commands.Bot(command_prefix="/", intents=intents)

#Configuration mysql

config_mysql = {
    "user": db_user,
    "password": db_pass,
    "host": db_host,
    "database": db_name,
}

def get_emoji_code(metier):
    metier_emojis = {
        'paysan': ':ear_of_rice:',
        'boulanger': ':bread:',
        'bijoutier': ':ring:',
        'bûcheron': ':deciduous_tree:',
        'cordonnier': ':boot:',
        'mineur': ':pick:',
        'tailleur': ':scissors:',
        'chasseur': ':bow_and_arrow:',
        'boucher': ':cut_of_meat:',
        'sculpteur d\'arc': ':archery:',
        'sculpteur de bâton': ':wood:',
        'sculpteur de baguette': ':magic_wand:',
        'pêcheur': ':fishing_pole_and_fish:',
        'poissonnier': ':fish:',
        'forgeur de dague': ':dagger:',
        'forgeur de marteau': ':hammer:',
        'forgeur d\'épée': ':crossed_swords:',
        'forgeur de pelle': ':pick:',
        'forgeur de hache': ':axe:',
        'alchimiste': ':alembic:',
        'forgeur de bouclier': ':shield:',
        'bricoleur': ':wrench:',
        'sculptemage d\'arc': ':dart:',
        'sculptemage de bâton': ':wood:',
        'sculptemage de baguette': ':magic_wand:',
        'joaillomage': ':gem:',
        'cordomage': ':thread:',
        'costumage': ':kimono:',
        'forgemage de dague': ':dagger:',
        'forgemage de marteau': ':hammer:',
        'forgemage d\'épée': ':crossed_swords:',
        'forgemage de pelle': ':pick:',
        'forgemage de hache': ':axe:'
    }

    # Normaliser le nom du métier
    metier = metier.lower().strip()

    # Vérifier si le métier est dans le dictionnaire
    if metier in metier_emojis:
        return metier_emojis[metier]
    else:
        return None



class MonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await self.handle_unknown_command(ctx)
            
    def add_custom_commands(self):
        self.bot.add_command(self.help_command)

    @commands.command(name='assist')
    async def help_command(self, ctx):
        embed = discord.Embed(title="Commandes disponibles", description="Voici les commandes disponibles :", color=0x00ff00)

        # Ajoutez des champs pour chaque commande avec une brève description
        embed.add_field(name="/addMetier <metier> <lvl>", value="Enregistre un métier avec un niveau.")
        embed.add_field(name="/updateMetier <metier> <lvl>", value="Met à jour le niveau d'un métier enregistré.")
        embed.add_field(name="/searchMetier <metier>", value="Recherche et affiche les utilisateurs avec un métier spécifique.")
        embed.add_field(name="/deleteMetier <metier>", value="Supprime un métier enregistré.")
        embed.add_field(name="/addMetierFor <TAG UNE PERSONNE> <metier> <lvl>", value="Enregistre un métier pour un utilisateur spécifié.")
        embed.add_field(name="/listMetier", value="Voir tous les métiers possible")

        await ctx.send(embed=embed)
    

    async def handle_unknown_command(self, ctx):
        await ctx.send("Oh guignol j'connais pas cette commande, utilise /assist ou ferme-la")



@bot.command(name='addMetier', aliases=['addMetierSuggestion'])
async def addMetier(ctx, *, args):
    try:
        # Diviser les arguments
        arguments = args.split()

        # Vérifier s'il y a suffisamment d'arguments
        if len(arguments) >= 2:
            profession = ' '.join(arguments[:-1])  # Tout sauf le dernier argument est le nom du métier
            profession = normalize_apostrophe(profession)
            niveau = arguments[-1]  # Le dernier argument est le niveau

            # Connexion à la base de données
            connexion_mysql = mysql.connector.connect(**config_mysql)

            # Récupération de l'ID de l'utilisateur Discord qui a rentré la commande
            discord_user_id = ctx.author.id

            # Vérifier si le métier est valide en le comparant avec la table possibleMetiers
            requete_validite_metier = "SELECT COUNT(*) as total FROM possibleMetiers WHERE name = %s"
            valeurs_validite_metier = (profession.capitalize(),)

            curseur_validite_metier = connexion_mysql.cursor(dictionary=True)
            curseur_validite_metier.execute(requete_validite_metier, valeurs_validite_metier)
            validite_metier_resultat = curseur_validite_metier.fetchone()
            total_validite_metier = validite_metier_resultat["total"]
            curseur_validite_metier.close()

            if not total_validite_metier:
                await ctx.send(f"{profession.capitalize()} n'est pas un métier valide. Veuillez choisir parmi les métiers disponibles.")
            else:
                # Exécution de la requête SQL pour vérifier si le métier existe déjà
                requete_existence = "SELECT COUNT(*) as total FROM metiers WHERE user = %s AND metierName = %s"
                valeurs_existence = (discord_user_id, profession.capitalize())

                curseur_existence = connexion_mysql.cursor(dictionary=True)
                curseur_existence.execute(requete_existence, valeurs_existence)
                existence_resultat = curseur_existence.fetchone()
                total_existence = existence_resultat["total"]
                curseur_existence.close()

                if total_existence:
                    await ctx.send(f"Vous avez déjà enregistré le métier de {profession.capitalize()}. Utilisez /update {profession.capitalize()} <niveau> pour mettre à jour le niveau.")
                else:
                    # Exécution de la requête SQL pour enregistrer le métier pour l'utilisateur
                    requete_enregistrement = "INSERT INTO metiers VALUES (%s, %s, %s)"
                    valeurs_enregistrement = (discord_user_id, profession.capitalize(), niveau)

                    curseur_enregistrement = connexion_mysql.cursor(dictionary=True)
                    curseur_enregistrement.execute(requete_enregistrement, valeurs_enregistrement)
                    connexion_mysql.commit()  # Committer la transaction pour appliquer les changements
                    curseur_enregistrement.close()

                    await ctx.send(f"Le métier de {profession.capitalize()} a été enregistré avec succès.")

        else:
            await ctx.send("Veuillez fournir le nom du métier et le niveau.")

    except mysql.connector.Error as err:
        # Gérer les erreurs de connexion MySQL
        print(f"Erreur de connexion MySQL : {err}")
        await ctx.send("Erreur de connexion à la base de données. Veuillez réessayer plus tard.")
    finally:
        # Fermer la connexion à la base de données dans tous les cas
        connexion_mysql.close()



def normalize_apostrophe(text):
    # Remplacez différentes formes d'apostrophes par une apostrophe simple
    normalized_text = text.replace('‘', "'").replace('’', "'").replace('`', "'").replace('´', "'")
    return normalized_text




@bot.command(name='updateMetier')
async def updateMetier(ctx, *, args):
    try:
        # Connexion à la base de données
        connexion_mysql = mysql.connector.connect(**config_mysql)

        # Récupération de l'ID de l'utilisateur Discord qui a rentré la commande
        discord_user_id = ctx.author.id

        # Diviser les arguments
        arguments = args.split()

        # Vérifier s'il y a suffisamment d'arguments
        if len(arguments) >= 2:
            profession = ' '.join(arguments[:-1])  # Tout sauf le dernier argument est le nom du métier
            profession = normalize_apostrophe(profession)
            niveau = arguments[-1]  # Le dernier argument est le niveau

            # Normaliser le nom du métier
            profession = normalize_apostrophe(profession)

            # Vérifier si le métier existe déjà pour l'utilisateur
            requete_existence = "SELECT COUNT(*) as total FROM metiers WHERE user = %s AND metierName = %s"
            valeurs_existence = (discord_user_id, profession.capitalize())

            curseur_existence = connexion_mysql.cursor(dictionary=True)
            curseur_existence.execute(requete_existence, valeurs_existence)
            existence_resultat = curseur_existence.fetchone()
            total_existence = existence_resultat["total"]
            curseur_existence.close()

            if total_existence:
                # Le métier existe, mise à jour du niveau
                requete_update = "UPDATE metiers SET niveau = %s WHERE user = %s AND metierName = %s"
                valeurs_update = (niveau, discord_user_id, profession.capitalize())

                curseur_update = connexion_mysql.cursor(dictionary=True)
                curseur_update.execute(requete_update, valeurs_update)
                connexion_mysql.commit()  # Committer la transaction pour appliquer les changements
                curseur_update.close()

                await ctx.send(f"Le niveau du métier {profession.capitalize()} a été mis à jour avec succès.")
            else:
                await ctx.send(f"Vous n'avez pas encore le métier de {profession.capitalize()} enregistré. Vous pouvez l'enregistrer en utilisant la commande : `/addMetier {profession.capitalize()} {niveau}`.")
        else:
            await ctx.send("Veuillez fournir le nom du métier et le niveau.")

    except mysql.connector.Error as err:
        # Gérer les erreurs de connexion MySQL
        print(f"Erreur de connexion MySQL : {err}")
        await ctx.send("Erreur de connexion à la base de données. Veuillez réessayer plus tard.")
    finally:
        # Fermer la connexion à la base de données dans tous les cas
        connexion_mysql.close()




@bot.command(name='searchMetier')
async def searchMetier(ctx, *, profession):
    try:
        # Connexion à la base de données
        connexion_mysql = mysql.connector.connect(**config_mysql)
            
        # Normaliser le nom du métier
        profession = normalize_apostrophe(profession)

        # Récupération des utilisateurs avec le métier spécifique, triés par niveau décroissant
        requete_sql = "SELECT user, niveau FROM metiers WHERE metierName = %s ORDER BY niveau DESC"
        valeurs = (profession.capitalize(),)

        curseur = connexion_mysql.cursor(dictionary=True)
        curseur.execute(requete_sql, valeurs)
        resultats = curseur.fetchall()
        curseur.close()

        if resultats:
            # Organiser les résultats par niveau
            niveaux_utilisateurs = {}
            for resultat in resultats:
                niveau = resultat['niveau']
                utilisateur_id = resultat['user']

                # Récupérer l'objet Member
                utilisateur = ctx.guild.get_member(utilisateur_id)

                if utilisateur:
                    utilisateur_nom = utilisateur.display_name
                else:
                    utilisateur_nom = f"Utilisateur inconnu ({utilisateur_id})"

                if niveau not in niveaux_utilisateurs:
                    niveaux_utilisateurs[niveau] = []
                niveaux_utilisateurs[niveau].append(utilisateur_nom)

            # Créer le message de sortie
            message_sortie = f"Joueurs ayant le métier '{profession.capitalize()}' et leurs niveaux :\n"

            for niveau, utilisateurs in niveaux_utilisateurs.items():
                utilisateurs_str = "\n    ".join(utilisateurs)
                message_sortie += f"\nlvl {str(niveau)} :\n    {utilisateurs_str}"

            await ctx.send(message_sortie)

        else:
            await ctx.send(f"Aucun joueur trouvé avec le métier '{profession.capitalize()}'.")

    except mysql.connector.Error as err:
        # Gérer les erreurs de connexion MySQL
        print(f"Erreur de connexion MySQL : {err}")
        await ctx.send("Erreur de connexion à la base de données. Veuillez réessayer plus tard.")
    finally:
        # Fermer la connexion à la base de données dans tous les cas
        connexion_mysql.close()





@tasks.loop(hours=336)  # 336 heures = 2 semaines
async def search_all_metier_task():
    await bot.wait_until_ready()

    try:
        # Connexion à la base de données
        connexion_mysql = mysql.connector.connect(**config_mysql)
            
        # Récupération de tous les métiers distincts
        requete_sql = "SELECT DISTINCT metierName FROM metiers"
        curseur = connexion_mysql.cursor()
        curseur.execute(requete_sql)
        metiers = [resultat[0] for resultat in curseur.fetchall()]
        curseur.close()

        if metiers:
            # Créer le message de sortie
            message_sortie = "Liste de tous les métiers et niveaux :\n"

            for metier in metiers:
                # Récupération des utilisateurs avec le métier spécifique, triés par niveau décroissant
                requete_sql_metier = "SELECT user, niveau FROM metiers WHERE metierName = %s ORDER BY niveau DESC"
                valeurs_metier = (metier,)

                curseur_metier = connexion_mysql.cursor(dictionary=True)
                curseur_metier.execute(requete_sql_metier, valeurs_metier)
                resultats_metier = curseur_metier.fetchall()
                curseur_metier.close()

                if resultats_metier:
                    emoji_code = get_emoji_code(metier)
                    if emoji_code:
                        message_sortie += f"\n\n{emoji_code} **{metier.capitalize()}** {emoji_code} :\n"

                        niveaux_utilisateurs = {}
                        for resultat in resultats_metier:
                            niveau = resultat['niveau']
                            utilisateur_id = resultat['user']

                            # Récupérer l'objet Member à partir du serveur
                            serveur = bot.get_guild(1179537413505298502)  # Remplacez SERVEUR_ID par l'ID de votre serveur
                            utilisateur = serveur.get_member(utilisateur_id)

                            if utilisateur:
                                utilisateur_nom = utilisateur.display_name
                            else:
                                utilisateur_nom = f"Utilisateur inconnu ({utilisateur_id})"

                            if niveau not in niveaux_utilisateurs:
                                niveaux_utilisateurs[niveau] = []
                            niveaux_utilisateurs[niveau].append(utilisateur_nom)

                        for niveau, utilisateurs in niveaux_utilisateurs.items():
                            utilisateurs_str = "\n        ".join(utilisateurs)
                            message_sortie += f"\n    lvl {str(niveau)} :\n        {utilisateurs_str}"

            # Envoyer le message dans le canal défini
            channel_id = 1179537759837376572  # Remplacez avec l'ID du canal où vous voulez envoyer le résultat
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send(message_sortie)

        else:
            print("Aucun métier trouvé dans la base de données.")

    except mysql.connector.Error as err:
        # Gérer les erreurs de connexion MySQL
        print(f"Erreur de connexion MySQL : {err}")
        print("Erreur lors de l'exécution de la tâche planifiée search_all_metier_task.")

    finally:
        if 'connexion_mysql' in locals() and connexion_mysql.is_connected():
            connexion_mysql.close()






@bot.command(name='deleteMetier')
async def deleteMetier(ctx, *, profession):
    try:
        # Connexion à la base de données
        connexion_mysql = mysql.connector.connect(**config_mysql)
        
        # Récupération de l'ID de l'utilisateur Discord qui a rentré la commande
        discord_user_id = ctx.author.id

        # Normaliser le nom du métier
        profession = normalize_apostrophe(profession)

        # Exécution de la requête SQL pour vérifier si le métier existe
        requete_existence = "SELECT COUNT(*) as total FROM metiers WHERE user = %s AND metierName = %s"
        valeurs_existence = (discord_user_id, profession.capitalize())

        curseur_existence = connexion_mysql.cursor(dictionary=True)
        curseur_existence.execute(requete_existence, valeurs_existence)
        existence_resultat = curseur_existence.fetchone()
        total_existence = existence_resultat["total"]
        curseur_existence.close()

        if total_existence:
            # Exécution de la requête SQL pour supprimer le métier
            requete_suppression = "DELETE FROM metiers WHERE user = %s AND metierName = %s"
            valeurs_suppression = (discord_user_id, profession.capitalize())

            curseur_suppression = connexion_mysql.cursor(dictionary=True)
            curseur_suppression.execute(requete_suppression, valeurs_suppression)
            connexion_mysql.commit()  # Committer la transaction pour appliquer les changements
            curseur_suppression.close()

            await ctx.send(f"Le métier de {profession.capitalize()} a été supprimé avec succès.")
        else:
            await ctx.send(f"Vous n'avez pas enregistré le métier de {profession.capitalize()}.")

    except mysql.connector.Error as err:
        # Gérer les erreurs de connexion MySQL
        print(f"Erreur de connexion MySQL : {err}")
        await ctx.send("Erreur de connexion à la base de données. Veuillez réessayer plus tard.")
    finally:
        # Fermer la connexion à la base de données dans tous les cas
        connexion_mysql.close()



@bot.command(name='addMetierFor', aliases=['addMetierForSuggestion'])
async def addMetierFor(ctx, member: discord.Member, *, args):
    try:
        # Diviser les arguments
        arguments = args.split()

        # Vérifier s'il y a suffisamment d'arguments
        if len(arguments) >= 2:
            profession = ' '.join(arguments[:-1])  # Tout sauf le dernier argument est le nom du métier
            profession = normalize_apostrophe(profession)
            niveau = arguments[-1]  # Le dernier argument est le niveau

            # Connexion à la base de données
            connexion_mysql = mysql.connector.connect(**config_mysql)

            # Récupération de l'ID de l'utilisateur Discord mentionné
            discord_user_id = member.id

            # Vérifier si le métier est valide en le comparant avec la table possibleMetiers
            requete_validite_metier = "SELECT COUNT(*) as total FROM possibleMetiers WHERE name = %s"
            valeurs_validite_metier = (profession.capitalize(),)

            curseur_validite_metier = connexion_mysql.cursor(dictionary=True)
            curseur_validite_metier.execute(requete_validite_metier, valeurs_validite_metier)
            validite_metier_resultat = curseur_validite_metier.fetchone()
            total_validite_metier = validite_metier_resultat["total"]
            curseur_validite_metier.close()

            if not total_validite_metier:
                await ctx.send(f"{profession.capitalize()} n'est pas un métier valide. Veuillez choisir parmi les métiers disponibles.")
            else:
                # Exécution de la requête SQL pour vérifier si le métier existe déjà
                requete_existence = "SELECT COUNT(*) as total FROM metiers WHERE user = %s AND metierName = %s"
                valeurs_existence = (discord_user_id, profession.capitalize())

                curseur_existence = connexion_mysql.cursor(dictionary=True)
                curseur_existence.execute(requete_existence, valeurs_existence)
                existence_resultat = curseur_existence.fetchone()
                total_existence = existence_resultat["total"]
                curseur_existence.close()

                if total_existence:
                    await ctx.send(f"{member.mention} a déjà enregistré le métier de {profession.capitalize()}. Utilisez /update {profession.capitalize()} <niveau> pour mettre à jour le niveau.")
                else:
                    # Exécution de la requête SQL pour enregistrer le métier pour l'utilisateur
                    requete_enregistrement = "INSERT INTO metiers VALUES (%s, %s, %s)"
                    valeurs_enregistrement = (discord_user_id, profession.capitalize(), niveau)

                    curseur_enregistrement = connexion_mysql.cursor(dictionary=True)
                    curseur_enregistrement.execute(requete_enregistrement, valeurs_enregistrement)
                    connexion_mysql.commit()  # Committer la transaction pour appliquer les changements
                    curseur_enregistrement.close()

                    await ctx.send(f"Le métier de {profession.capitalize()} pour {member.mention} a été enregistré avec succès.")

        else:
            await ctx.send("Veuillez fournir le nom du métier et le niveau.")

    except mysql.connector.Error as err:
        # Gérer les erreurs de connexion MySQL
        print(f"Erreur de connexion MySQL : {err}")
        await ctx.send("Erreur de connexion à la base de données. Veuillez réessayer plus tard.")
    finally:
        # Fermer la connexion à la base de données dans tous les cas
        connexion_mysql.close()


@bot.command(name='listMetier')
async def listMetier(ctx):
    try:
        # Connexion à la base de données
        connexion_mysql = mysql.connector.connect(**config_mysql)

        # Exécution de la requête SQL pour récupérer tous les métiers possibles
        requete_liste_metiers = "SELECT name FROM possibleMetiers"

        curseur_liste_metiers = connexion_mysql.cursor(dictionary=True)
        curseur_liste_metiers.execute(requete_liste_metiers)
        liste_metiers_resultat = curseur_liste_metiers.fetchall()
        curseur_liste_metiers.close()

        if liste_metiers_resultat:
            liste_metiers = [metier["name"] for metier in liste_metiers_resultat]
            await ctx.send("Liste des métiers possibles :\n" + "\n".join(liste_metiers))
        else:
            await ctx.send("Aucun métier n'est disponible.")

    except mysql.connector.Error as err:
        # Gérer les erreurs de connexion MySQL
        print(f"Erreur de connexion MySQL : {err}")
        await ctx.send("Erreur de connexion à la base de données. Veuillez réessayer plus tard.")
    finally:
        # Fermer la connexion à la base de données dans tous les cas
        connexion_mysql.close()







@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user.name}")

    # Connexion à la base de données
    connexion_mysql = mysql.connector.connect(**config_mysql)

    try:
        # Vérifier si la table 'metiers' existe déjà
        table_existence_query = "SHOW TABLES LIKE 'metiers';"
        curseur_existence = connexion_mysql.cursor()
        curseur_existence.execute(table_existence_query)
        table_existante = curseur_existence.fetchone()
        curseur_existence.close()

        if not table_existante:
            # La table 'metiers' n'existe pas, on la crée
            table_creation_query = """
            CREATE TABLE metiers (
                user BIGINT NOT NULL,
                metierName VARCHAR(255) NOT NULL,
                niveau INT NOT NULL,
                PRIMARY KEY (user, metierName)
            );
            """
            try:
                curseur = connexion_mysql.cursor()
                curseur.execute(table_creation_query)
                print("Table 'metiers' créée avec succès.")
            except mysql.connector.Error as err:
                print(f"Erreur lors de la création de la table 'metiers': {err}")

        # Création de la table 'possibleMetiers' avec les métiers de base (si elle n'existe pas déjà)
        table_existence_query = "SHOW TABLES LIKE 'possibleMetiers';"
        curseur_existence = connexion_mysql.cursor()
        curseur_existence.execute(table_existence_query)
        table_existante = curseur_existence.fetchone()
        curseur_existence.close()
        
        if not table_existante :
            table_metiers_possibles_query = """
            CREATE TABLE IF NOT EXISTS possibleMetiers (
                name VARCHAR(255) NOT NULL,
                PRIMARY KEY (name)
            );
            """
            metiers_possibles = [
                'Paysan', 'Boulanger', 'Bijoutier', 'Bûcheron', 'Cordonnier', 'Mineur', 'Tailleur',
                'Chasseur', 'Boucher', 'Sculpteur d\'arc', 'Sculpteur de bâton', 'Sculpteur de baguette',
                'Pêcheur', 'Poissonnier', 'Forgeur de dague', 'Forgeur de marteau', 'Forgeur d\'épée',
                'Forgeur de pelle', 'Forgeur de hache', 'Alchimiste', 'Forgeur de bouclier', 'Bricoleur',
                'Sculptemage d\'arc', 'Sculptemage de bâton', 'Sculptemage de baguette', 'Joaillomage',
                'Cordomage', 'Costumage', 'Forgemage de dague', 'Forgemage de marteau', 'Forgemage d\'épée',
                'Forgemage de pelle', 'Forgemage de hache'
            ]

            try:
                curseur_metiers_possibles = connexion_mysql.cursor()
                curseur_metiers_possibles.execute(table_metiers_possibles_query)
              
                # Insérer les valeurs uniquement si la table a été créée
                for metier in metiers_possibles:
                    insert_query = "INSERT INTO possibleMetiers (name) VALUES (%s)"
                    valeurs_insert = (metier,)
                    curseur_insert = connexion_mysql.cursor(dictionary=True)
                    curseur_insert.execute(insert_query, valeurs_insert)
                    connexion_mysql.commit()
                    print(f"Metier {metier} créé dans la table")
                print("Table 'possibleMetiers' créée avec succès.")
        
            except mysql.connector.Error as err:
                print(f"Erreur lors de la création de la table 'possibleMetiers': {err}")
        
        cog = MonCog(bot)
        await bot.add_cog(cog)
        search_all_metier_task.start()

    finally:
        # Fermez la connexion à la base de données dans tous les cas
        connexion_mysql.close()






bot.run(bot_token)