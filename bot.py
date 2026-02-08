import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
import sqlite3
from datetime import datetime
import config

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# BASE DE DATOS
# =========================
db = sqlite3.connect("puntos.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS puntos (
    user_id INTEGER PRIMARY KEY,
    puntos INTEGER
)
""")
db.commit()


def sumar_puntos(user_id, cantidad):
    cursor.execute("SELECT puntos FROM puntos WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute(
            "UPDATE puntos SET puntos = puntos + ? WHERE user_id = ?",
            (cantidad, user_id)
        )
    else:
        cursor.execute(
            "INSERT INTO puntos (user_id, puntos) VALUES (?, ?)",
            (user_id, cantidad)
        )
    db.commit()


def obtener_puntos(user_id):
    cursor.execute("SELECT puntos FROM puntos WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else 0


def eliminar_puntos(user_id):
    cursor.execute("DELETE FROM puntos WHERE user_id = ?", (user_id,))
    db.commit()


# =========================
# READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot conectado como {bot.user}")


# =========================
# MODAL DE PUNTOS
# =========================
class PuntosModal(Modal, title="Asignar puntos"):
    puntos = TextInput(label="¿Cuántos puntos?", placeholder="Ej: 5", required=True)

    def __init__(self, usuario, embed, mensaje, trabajo):
        super().__init__()
        self.usuario = usuario
        self.embed = embed
        self.mensaje = mensaje
        self.trabajo = trabajo

    async def on_submit(self, interaction: discord.Interaction):
        cantidad = int(self.puntos.value)
        sumar_puntos(self.usuario.id, cantidad)

        self.embed.set_field_at(3, name="Estado", value="✅ Aceptado", inline=False)
        await self.mensaje.edit(embed=self.embed, view=None)

        canal_resultados = interaction.client.get_channel(
            config.CANAL_TRABAJOS_RESULTADO
        )

        await canal_resultados.send(
            f"✅ **Trabajo aceptado**\n"
            f"👤 Usuario: {self.usuario.mention}\n"
            f"🛠️ Trabajo: **{self.trabajo}**\n"
            f"⭐ Puntos otorgados: **{cantidad}**"
        )

        await interaction.response.send_message(
            "✅ Trabajo aceptado y puntos asignados.",
            ephemeral=True
        )


# =========================
# BOTONES
# =========================
class RevisionView(View):
    def __init__(self, usuario, embed, mensaje, trabajo):
        super().__init__(timeout=None)
        self.usuario = usuario
        self.embed = embed
        self.mensaje = mensaje
        self.trabajo = trabajo

    @discord.ui.button(label="Aceptar", style=discord.ButtonStyle.success)
    async def aceptar(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(
            PuntosModal(self.usuario, self.embed, self.mensaje, self.trabajo)
        )

    @discord.ui.button(label="Denegar", style=discord.ButtonStyle.danger)
    async def denegar(self, interaction: discord.Interaction, button: Button):
        self.embed.set_field_at(3, name="Estado", value="❌ Denegado", inline=False)
        await self.mensaje.edit(embed=self.embed, view=None)

        canal_resultados = interaction.client.get_channel(
            config.CANAL_TRABAJOS_RESULTADO
        )

        await canal_resultados.send(
            f"❌ **Trabajo denegado**\n"
            f"👤 Usuario: {self.usuario.mention}\n"
            f"🛠️ Trabajo: **{self.trabajo}**"
        )

        await interaction.response.send_message(
            "❌ Trabajo denegado.",
            ephemeral=True
        )


# =========================
# /trabajo
# =========================
@bot.tree.command(name="trabajo", description="Enviar trabajo del staff")
@app_commands.describe(
    tipo="Tipo de trabajo",
    evidencia="Imagen de evidencia"
)
async def trabajo(
    interaction: discord.Interaction,
    tipo: str,
    evidencia: discord.Attachment
):
    canal = bot.get_channel(config.CANAL_REVISION_TRABAJOS)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    embed = discord.Embed(
        title="📋 Nuevo trabajo",
        color=discord.Color.orange()
    )
    embed.add_field(name="Usuario", value=interaction.user.mention, inline=False)
    embed.add_field(name="Trabajo", value=tipo, inline=False)
    embed.add_field(name="Evidencia", value=evidencia.url, inline=False)
    embed.add_field(name="Estado", value="⏳ Esperando validación", inline=False)
    embed.add_field(name="Fecha", value=fecha, inline=False)

    msg = await canal.send(embed=embed)
    await msg.edit(view=RevisionView(interaction.user, embed, msg, tipo))

    await interaction.response.send_message(
        "🕒 Tu trabajo está siendo validado por el Alto Mando.",
        ephemeral=True
    )


# =========================
# /puntos
# =========================
@bot.tree.command(name="puntos", description="Ver puntos de un usuario")
async def puntos(interaction: discord.Interaction, usuario: discord.Member):
    pts = obtener_puntos(usuario.id)
    await interaction.response.send_message(
        f"⭐ {usuario.mention} tiene **{pts} puntos**."
    )


# =========================
# /puntos-eliminar
# =========================
@bot.tree.command(name="puntos-eliminar", description="Eliminar puntos de un usuario")
async def puntos_eliminar(interaction: discord.Interaction, usuario: discord.Member):
    eliminar_puntos(usuario.id)
    await interaction.response.send_message(
        f"🗑️ Puntos de {usuario.mention} eliminados."
    )


# =========================
# /ascender
# =========================
@bot.tree.command(name="ascender", description="Ascender a un usuario")
async def ascender(interaction: discord.Interaction, usuario: discord.Member, posicion: str):
    canal = bot.get_channel(config.CANAL_ASCENSOS)
    await canal.send(
        f"📈 El usuario {usuario.mention} ha sido **ascendido a {posicion}** por {interaction.user.mention}!"
    )
    await interaction.response.send_message("✅ Ascenso anunciado.", ephemeral=True)


# =========================
# /descender
# =========================
@bot.tree.command(name="descender", description="Descender a un usuario")
async def descender(interaction: discord.Interaction, usuario: discord.Member, posicion: str):
    canal = bot.get_channel(config.CANAL_ASCENSOS)
    await canal.send(
        f"📉 El usuario {usuario.mention} ha sido **destituido a {posicion}** por {interaction.user.mention}!"
    )
    await interaction.response.send_message("✅ Descenso anunciado.", ephemeral=True)


# =========================
# RUN
# =========================
bot.run(config.TOKEN)
