import discord
from discord.ext import commands
from discord import app_commands
import os
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv("MTQ2OTgxMDkyMzUyNjAzMzUzMA.GnpvkA.bIEtdKwWnghQEwfLK-XjsSp2ivQV48pX-SVg90")  # <- GitHub Secret
GUILD_ID = 1059793781458743326  # Cambia por tu server ID

# --- BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- ALMACENAMIENTO EN MEMORIA ---
# Diccionario de puntos, temporal (se reinicia si el bot se reinicia)
puntos = {}

# Diccionario temporal de trabajos en validación
trabajos_pendientes = {}

# --- EVENTOS ---
@bot.event
async def on_ready():
    print(f"{bot.user} listo")
    try:
        guild = discord.Object(id=GUILD_ID)
        await bot.tree.sync(guild=guild)
        print("Comandos sincronizados")
    except Exception as e:
        print(f"Error sincronizando comandos: {e}")

# --- COMANDOS ---

# /trabajo
@bot.tree.command(name="trabajo", description="Enviar un trabajo para validación")
@app_commands.describe(tipo="Tipo de trabajo", evidencia="Evidencia (link o imagen)")
async def trabajo(interaction: discord.Interaction, tipo: str, evidencia: str):
    user = interaction.user
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    # Mensaje de confirmación al usuario
    await interaction.response.send_message("Tu trabajo está siendo validado por el Alto Mando.", ephemeral=True)

    # Mensaje al canal de trabajos (cambia el ID)
    canal_trabajos = bot.get_channel(123456789012345678)
    if canal_trabajos is None:
        print("No se encontró el canal de trabajos")
        return

    embed = discord.Embed(title="Nuevo trabajo", color=discord.Color.blue())
    embed.add_field(name="Usuario", value=user.mention, inline=False)
    embed.add_field(name="Trabajo", value=tipo, inline=False)
    embed.add_field(name="Evidencia", value=evidencia, inline=False)
    embed.add_field(name="Estado", value="Esperando validación", inline=False)
    embed.add_field(name="Fecha", value=fecha, inline=False)

    # Botones aceptar / denegar
    class TrabajoView(discord.ui.View):
        @discord.ui.button(label="Aceptar", style=discord.ButtonStyle.green)
        async def aceptar(self, button: discord.ui.Button, button_interaction: discord.Interaction):
            # Preguntar puntos
            await button_interaction.response.send_message("¿Cuántos puntos quieres dar?", ephemeral=True)
            # Para simplificar, damos 1 punto por defecto
            puntos[user.id] = puntos.get(user.id, 0) + 1
            embed.set_field_at(3, name="Estado", value="Aceptado", inline=False)
            await msg.edit(embed=embed, view=None)

        @discord.ui.button(label="Denegar", style=discord.ButtonStyle.red)
        async def denegar(self, button: discord.ui.Button, button_interaction: discord.Interaction):
            embed.set_field_at(3, name="Estado", value="Denegado", inline=False)
            await msg.edit(embed=embed, view=None)

    view = TrabajoView()
    msg = await canal_trabajos.send(embed=embed, view=view)

# /puntos
@bot.tree.command(name="puntos", description="Ver puntos de un usuario")
@app_commands.describe(usuario="Usuario a revisar")
async def puntos_cmd(interaction: discord.Interaction, usuario: discord.Member):
    total = puntos.get(usuario.id, 0)
    await interaction.response.send_message(f"{usuario.mention} tiene {total} puntos.", ephemeral=True)

# /puntos-eliminar
@bot.tree.command(name="puntos-eliminar", description="Eliminar puntos de un usuario")
@app_commands.describe(usuario="Usuario a reiniciar puntos")
async def puntos_eliminar(interaction: discord.Interaction, usuario: discord.Member):
    if usuario.id in puntos:
        puntos[usuario.id] = 0
    await interaction.response.send_message(f"Puntos de {usuario.mention} eliminados.", ephemeral=True)

# /ascender
@bot.tree.command(name="ascender", description="Ascender un usuario")
@app_commands.describe(usuario="Usuario a ascender", posicion="Nueva posición")
async def ascender(interaction: discord.Interaction, usuario: discord.Member, posicion: str):
    canal = bot.get_channel(123456789012345678)  # Canal donde anunciar ascensos
    if canal:
        await canal.send(f"El usuario {usuario.mention} ha sido **ascendido** a {posicion} por {interaction.user.mention}!")

# /descender
@bot.tree.command(name="descender", description="Descender un usuario")
@app_commands.describe(usuario="Usuario a descender", posicion="Posición anterior")
async def descender(interaction: discord.Interaction, usuario: discord.Member, posicion: str):
    canal = bot.get_channel(123456789012345678)  # Canal donde anunciar descensos
    if canal:
        await canal.send(f"El usuario {usuario.mention} ha sido **destituido** de {posicion} por {interaction.user.mention}!")

# --- EJECUTAR BOT ---
bot.run(TOKEN)


