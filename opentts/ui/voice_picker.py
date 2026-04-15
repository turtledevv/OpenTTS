import discord
from ..core.settings import update_user_setting


def _group_by_language(voices: list[dict]) -> dict[str, list[str]]:
    """Returns {'en': ['en-US', 'en-GB', ...], 'es': [...], ...}"""
    groups: dict[str, list[str]] = {}
    for v in voices:
        lang = v["Locale"].split("-")[0]
        locale = v["Locale"]
        if lang not in groups:
            groups[lang] = []
        if locale not in groups[lang]:
            groups[lang].append(locale)
    return {k: sorted(v) for k, v in sorted(groups.items())}


class LangSelect(discord.ui.Select):
    def __init__(self, groups: dict[str, list[str]], voices: list[dict]):
        self.groups = groups
        self.all_voices = voices
        options = [discord.SelectOption(label=lang, value=lang) for lang in list(groups)[:25]]
        super().__init__(placeholder="1️⃣  Pick a language…", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: VoicePickerView = self.view
        lang = self.values[0]
        locales = self.groups[lang]

        new_options = [discord.SelectOption(label=loc, value=loc) for loc in locales[:25]]
        view.locale_select.options = new_options
        view.locale_select.placeholder = "2️⃣  Pick a region…"
        view.locale_select.disabled = False
        view.voice_select.options = [discord.SelectOption(label="—", value="__none__")]
        view.voice_select.placeholder = "3️⃣  Pick a region first…"
        view.voice_select.disabled = True
        view.selected_voice = None
        view.confirm_btn.disabled = True

        await interaction.response.edit_message(view=view)


class LocaleSelect(discord.ui.Select):
    def __init__(self, all_voices: list[dict]):
        self.all_voices = all_voices
        super().__init__(
            placeholder="2️⃣  Pick a language first…",
            options=[discord.SelectOption(label="—", value="__none__")],
            disabled=True,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction):
        view: VoicePickerView = self.view
        locale = self.values[0]

        filtered = [v for v in self.all_voices if v["Locale"] == locale]
        new_options = [
            discord.SelectOption(label=v["ShortName"], value=v["ShortName"])
            for v in filtered[:25]
        ]
        view.voice_select.options = new_options
        view.voice_select.placeholder = "3️⃣  Pick a voice…"
        view.voice_select.disabled = False
        view.selected_voice = None
        view.confirm_btn.disabled = True

        await interaction.response.edit_message(view=view)


class VoiceSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="3️⃣  Pick a region first…",
            options=[discord.SelectOption(label="—", value="__none__")],
            disabled=True,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction):
        view: VoicePickerView = self.view
        view.selected_voice = self.values[0]
        view.confirm_btn.disabled = False
        await interaction.response.edit_message(view=view)


class ConfirmButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Set voice",
            style=discord.ButtonStyle.success,
            emoji="✅",
            disabled=True,
            row=3,
        )

    async def callback(self, interaction: discord.Interaction):
        view: VoicePickerView = self.view
        parts = (view.selected_voice or "").split("-", 2)
        if len(parts) == 3:
            update_user_setting(view.guild_id, view.user_id, "voice.lang",   parts[0])
            update_user_setting(view.guild_id, view.user_id, "voice.region", parts[1])
            update_user_setting(view.guild_id, view.user_id, "voice.name",   parts[2])
        view.stop()
        await interaction.response.edit_message(
            content=f"✅ Voice set to **{view.selected_voice}**",
            view=None,
        )


class VoicePickerView(discord.ui.View):
    def __init__(self, voices: list[dict], guild_id: int, user_id: int):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.user_id = user_id
        self.selected_voice: str | None = None

        groups = _group_by_language(voices)

        self.locale_select = LocaleSelect(voices)
        self.voice_select = VoiceSelect()
        self.confirm_btn = ConfirmButton()

        self.add_item(LangSelect(groups, voices))
        self.add_item(self.locale_select)
        self.add_item(self.voice_select)
        self.add_item(self.confirm_btn)