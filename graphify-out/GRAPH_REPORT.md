# Graph Report - pixel-ops  (2026-11-18)

## Corpus Check
- 323 files · ~204,524 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 5, .ini 3, .ttf 3)

## Summary
- 4134 nodes · 11170 edges · 232 communities (183 shown, 49 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 1139 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b5ef6a53`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- IntegrationContext
- App.tsx
- pc_stats.py
- codex_account.py
- PokemonAiPromptBuilder
- sprites.py
- EventBus
- WorkEvent
- ClickUpTaskSource
- AIUsageSnapshot
- configApi.ts
- test_spaceship.py
- hud.py
- PokeApiClient
- MapRouteManager
- App
- display
- pokemon/plugin.py
- devDependencies
- Agent Guide
- usb_bulk.py
- OverworldScene
- EventCategory
- compilerOptions
- DisplayOutputRow
- SlackAmbientAggregator
- LcdBleReceiver
- test_pr_arrivals.py
- PixelOpsEvent
- test_thermalright_usb.py
- VisualAndAiPluginTests
- CompanionSnapshot
- BaseWeatherSource
- overworld_scene.py
- crosshero.py
- app.mjs
- draw_hud
- datetime
- heltec-e213/src/main.cpp
- calendar.py
- eink_http.py
- SpaceshipEngine
- game
- LayoutPreview
- PixelOpsKiteHub
- esp32-c6-lcd-1.47/src/main.cpp
- steps
- steps
- gamification.py
- google_calendar.py
- discord/client.py
- ThermalrightUsbTransport
- datetime
- LocalMediaSource
- CalendarEventSource
- SpaceshipScene
- event_pokemon_types
- main
- main.cjs
- react
- codexAccount.ts
- handleHeartbeat
- vite.config.ts
- setup
- text_box.py
- IntegrationPanel
- DesktopManager
- renderStandalone
- test_lian_li_usb.py
- SpaceshipStateStore
- PokemonEngine
- adr/README.md
- Pixel OPs Config Studio
- encode_lcd_frame
- MovementAreaEditor
- HudBox
- pixelops-kite/package.json
- people
- thermalright_cli.py
- GamePhase
- DiscordGatewayClient
- AmbientSignal
- eslint.config.js
- manifest.json
- .start
- WindowOutput
- Pixel OPs
- account_hud.py
- service-worker.js
- thermalright_usb.py
- pokemon
- PixelOpsApp
- BrowserView
- WanderNavigator
- throttle
- events
- 0032 - Waveshare Bluetooth frame transport
- json
- encounter
- content-script.js
- ADR 0008: CrossHero fitness data enters as a daily observation
- ADR 0025: E-ink displays are hybrid network outputs
- ADR 0026: Color LCDs are network output terminals
- PokemonKnowledge
- 0009 - Meetings Are Ambient Ceremonies
- Pixel OPs — Heltec Vision Master E213
- LcdUsbOutput
- 0001 - Ambient Social Observability, Not Feeds
- 0037 - PR inventory is not a new arrival
- ThermalrightProtocol
- spaceship/plugin.py
- 0006 - Secrets Stay In Env, Runtime Toggles Move To JSON
- 0007 - AI Decisions Are Optional, Cached, And Throttled
- 0020 - Tasks HUDs Share Provider-Neutral Board State
- split_map_sheets.py
- Pokemon Plugin
- 0013 - Config Studio Discovers Plugin-Owned Config
- 0015 - Timezone Config Is Derived From IANA Selection
- 0016 - PC Stats Are Local Integration Metrics
- 0017 - Linux And Windows Are Supported Runtime Targets
- 0021 - Local Runtime State Uses SQLite
- ClickUpTaskSource
- 0027 - Spaceship Progress Is Active-Time And Game-Owned
- CalendarController
- 0031 - Waveshare LCD supports USB frame delivery
- Pixel OPs firmware for ESP32-C6-LCD-1.47
- ai_selector
- Pixel OPs Browser Bridge Extension
- CalendarEvent
- Windows Setup
- integration_plugins/registry.py
- Google Calendar account setup
- Spaceship game
- PixelOpsKite
- walk
- StandalonePage
- DiscordIntegrationPanel
- GitHubEventSource
- NOTICE.md
- 0002 - Provider Integrations Are Runtime Plugins
- TaskSnapshot
- emoji_image
- DisplayOutput
- Thermalright USB Plugin
- Linux Setup
- os
- splash.py
- inspect_packet
- ThermalrightOutput
- 0004 - Slack Uses Socket Mode Only
- start-pixel-ops-runtime.sh
- test_core.py
- build
- ProjectSnapshot
- lian_li_usb.py
- test_codex_status.py
- _PullFrameServer
- 0011 - Graphify Artifacts Document The Codebase Map
- TURZXOutput
- argparse
- 0036 - Windows desktop lifecycle is per-user
- desktop.py
- next_event
- startFirmwareOperation
- 0038 - Google Calendar uses read-only user OAuth
- PreviewOutput
- _PcHealthServer
- dataclasses
- scripts
- 0005 - JSON Runtime Configuration And Hot Reload
- ShowOffScenario
- 0023 - PixelOpsKite Relays Webhooks Over WebSocket
- 0034 - Account quota is a neutral observation
- FakeRPC
- 0033 — Token history HUD
- 0018 - ClickUp Tasks Are Planning Snapshots
- 0008 - Pokemon Is A Visual Plugin, Not The Integration Model
- 0041 - Lian Li native USB output
- ai_usage.py
- config-studio/package.json
- ScreenRotationController
- 0010 - Weather, Calendar, GitHub, Slack, Discord Share The Same Runtime Boundary
- discoverRuntimeProcess
- installRuntimeAutostart
- main.py
- font
- readDotEnv
- detectVisualPlugins
- runKiteCommand
- PixelOpsStateStore
- LcdBleOutput
- mac

## God Nodes (most connected - your core abstractions)
1. `OverworldScene` - 170 edges
2. `WorkEvent` - 130 edges
3. `App()` - 80 edges
4. `IntegrationContext` - 77 edges
5. `font()` - 67 edges
6. `CalendarEvent` - 66 edges
7. `IntegrationContribution` - 61 edges
8. `VisualAndAiPluginTests` - 60 edges
9. `EventCategory` - 59 edges
10. `WeatherState` - 56 edges

## Surprising Connections (you probably didn't know these)
- `Decision` --references--> `ConfigWatcher`  [INFERRED]
  docs/adr/0005-json-runtime-configuration-and-hot-reload.md → pixel_ops/config_loader.py
- `Runtime Architecture` --references--> `PixelOpsApp`  [INFERRED]
  README.md → pixel_ops/core/app.py
- `Decision` --references--> `AIQuotaSnapshot`  [INFERRED]
  docs/adr/0034-account-quota-is-a-neutral-observation.md → pixel_ops/data_sources/ai_quota.py
- `Consequences` --references--> `GamificationSnapshot`  [INFERRED]
  docs/adr/0024-gamification-hud-uses-provider-neutral-state.md → pixel_ops/data_sources/gamification.py
- `Context` --references--> `TaskSnapshot`  [INFERRED]
  docs/adr/0028-project-radar-uses-provider-neutral-observations.md → pixel_ops/data_sources/tasks.py

## Import Cycles
- None detected.

## Communities (232 total, 49 thin omitted)

### Community 0 - "IntegrationContext"
Cohesion: 0.08
Nodes (34): Architecture, Integration Plugins, ObservationEventSource, IntegrationContext, IntegrationContribution, IntegrationPlugin, AIUsageIntegrationPlugin, plugin() (+26 more)

### Community 1 - "App.tsx"
Cohesion: 0.05
Nodes (47): attachDisplayToNearest(), buildTimezoneOptions(), clampOverlapAxis(), compactTimezoneKey(), countryForTimezone(), displayDistance(), displayOverlapsAny(), emptyPerson() (+39 more)

### Community 2 - "pc_stats.py"
Cohesion: 0.08
Nodes (22): 0035 - Lian Li is a desktop output, Consequences, Context, Decision, _bytes_label(), _duration_label(), _linux_temperature_c(), _normalize_disk_path() (+14 more)

### Community 3 - "codex_account.py"
Cohesion: 0.11
Nodes (10): AIQuotaSnapshot, AccountController, AccountRPC, CodexAccountSource, main(), normalize_limits(), profile_lock(), profile_path() (+2 more)

### Community 4 - "PokemonAiPromptBuilder"
Cohesion: 0.12
Nodes (6): AiDecisionRequest, OpenAiChatGptPlugin, AiPokemonChoice, AiThrottle, _env_bool(), PokemonAiPromptBuilder

### Community 5 - "sprites.py"
Cohesion: 0.08
Nodes (25): palette_for_hour(), _apply_transparency(), ash_direction_frame(), ash_frame(), AshSpriteSet, battle_ash_frame(), _load_battle_ash_frames(), _load_pokeball_frames() (+17 more)

### Community 6 - "EventBus"
Cohesion: 0.07
Nodes (7): EventBus, DiscordGatewayAdapter, PixelOpsKiteClient, PixelOpsKiteEventSource, SlackBusEventSource, ZoomBusEventSource, _kite_zoom_envelope()

### Community 7 - "WorkEvent"
Cohesion: 0.11
Nodes (11): 0003 - Provider-Neutral Ambient Signals, Consequences, Context, Decision, WorkEvent, MockEventSource, EncounterSystem, _env_bool() (+3 more)

### Community 8 - "ClickUpTaskSource"
Cohesion: 0.28
Nodes (7): _assignee_label(), _bool_param(), _datetime_from_millis(), _order_parent_tasks_with_subtasks(), _task_from_payload(), _task_sort_key(), TaskItem

### Community 9 - "AIUsageSnapshot"
Cohesion: 0.15
Nodes (13): AIUsageSnapshot, _ai_usage_gauge_short_label(), _ai_usage_gauge_value(), _ai_usage_label(), _ai_usage_reset_countdown(), _ai_usage_used_label(), _draw_ai_usage_compact(), _draw_ai_usage_window() (+5 more)

### Community 10 - "configApi.ts"
Cohesion: 0.08
Nodes (34): loadNpcSpriteManifest(), ConfigDescriptor, ConfigManifest, CrossHeroSessionResponse, DetectedPlugin, DiscordGuildOption, DiscordOAuthStartResponse, DiscordOAuthStatusResponse (+26 more)

### Community 11 - "test_spaceship.py"
Cohesion: 0.07
Nodes (22): AsteroidRecord, _active_mining_asteroid(), _crew_assignment_room(), _crew_is_working(), _door_open_amount(), _doorway_crew_position(), _drone_progress(), _local_doorway_position() (+14 more)

### Community 12 - "hud.py"
Cohesion: 0.09
Nodes (40): CrossHeroWorkoutLine, _ai_mana_color(), _cache_asset_frames(), _crosshero_text_width(), _crosshero_wod_pages(), _draw_current_weather_metrics(), draw_eink_telemetry_huds(), _draw_media_thumbnail() (+32 more)

### Community 13 - "PokeApiClient"
Cohesion: 0.21
Nodes (4): Encounter, EncounterSpawner, PokeApiClient, Pokemon

### Community 14 - "MapRouteManager"
Cohesion: 0.11
Nodes (3): MapArea, MapRouteManager, walkable()

### Community 15 - "App"
Cohesion: 0.07
Nodes (41): App(), movePerson(), mutate(), persistConfig(), refreshConfig(), refreshFirmwareStatus(), refreshManifest(), refreshRuntimeAutostartStatus() (+33 more)

### Community 16 - "display"
Cohesion: 0.06
Nodes (34): api_key_env, cache_dir, cache_enabled, enabled, model, provider, reasoning_effort, timeout_seconds (+26 more)

### Community 17 - "pokemon/plugin.py"
Cohesion: 0.17
Nodes (5): AiDecisionPlugin, _flatten_companion_config(), plugin(), PokemonPlugin, test_plugin_uses_no_capture_store_ai_or_screen_rotation_in_show_off()

### Community 18 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, electron@^39.2.7, electron-builder@^26.0.12, eslint@^9.32.0, eslint-config-prettier@^10.1.1, @types/node@^22.16.5, @types/react@^19.2.0, @types/react-dom@^19.2.0 (+7 more)

### Community 19 - "Agent Guide"
Cohesion: 0.22
Nodes (8): Agent Guide, AI Calls, Configuration, Default Execution Standard, Documentation, Hot Reload, Product Direction, Running

### Community 20 - "usb_bulk.py"
Cohesion: 0.11
Nodes (9): image_to_rgb565(), Command, _device_selector_suffix(), _find_usb_device(), _safe_usb_string(), scan_turzx_devices(), _usb_claim_error_message(), UsbBulkDeviceInfo (+1 more)

### Community 21 - "OverworldScene"
Cohesion: 0.10
Nodes (3): OverworldScene, VoiceCompanionState, test_zoomed_scene_uses_native_sprite_scale_and_stays_put_for_encounters()

### Community 22 - "EventCategory"
Cohesion: 0.14
Nodes (16): EventCategory, EncounterContext, countdown_meeting(), KrakenProjection, get_pokemon(), scene(), state(), test_battle_interrupts_meeting_and_resumes_without_extending_it() (+8 more)

### Community 23 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+11 more)

### Community 24 - "DisplayOutputRow"
Cohesion: 0.18
Nodes (27): applyEquipment(), applyMultiDisplayBounds(), applyPrimaryDisplay(), cloneJson(), defaultEinkDeviceConfig(), defaultLayoutFor(), defaultLcdDeviceConfig(), defaultThermalrightDeviceConfig() (+19 more)

### Community 25 - "SlackAmbientAggregator"
Cohesion: 0.09
Nodes (12): BusEnvelope, _ChannelActivity, SlackAmbientAggregator, SlackChannelRule, _SummaryWindow, _actor(), classify_slack_event(), _slack_datetime() (+4 more)

### Community 26 - "LcdBleReceiver"
Cohesion: 0.05
Nodes (27): LcdBleReceiver, activeHandle_, buffer_, capacity_, checksum_, COMMAND, commandCallbacks_, DATA (+19 more)

### Community 27 - "test_pr_arrivals.py"
Cohesion: 0.11
Nodes (23): _event_weight(), _is_friday(), _metadata_types(), _sleepy_or_calm(), SocialWeatherSystem, WorldMoodState, apply_battle_ambience(), _draw_arena_marks() (+15 more)

### Community 28 - "PixelOpsEvent"
Cohesion: 0.07
Nodes (11): GameEngine, AIQuotaWindow, EventSource, PixelOpsEvent, PixelOpsEventKind, account(), test_compact_panel_keeps_exact_account_totals_and_reset_time(), test_reset_boundary_does_not_infer_new_allowance() (+3 more)

### Community 29 - "test_thermalright_usb.py"
Cohesion: 0.19
Nodes (14): dry_run_replay(), export_replay_json(), load_replay_file(), load_usbpcap_bulk_packets(), replay_packets(), ReplayOptions, ReplayPacket, build_parser() (+6 more)

### Community 30 - "VisualAndAiPluginTests"
Cohesion: 0.11
Nodes (9): PCStatsSnapshot, WeatherState, _capture_cause_label(), _capture_timestamp_label(), CapturedPokemonRecord, _compact_capture_context(), _parse_capture_datetime(), font_scale_for_canvas() (+1 more)

### Community 31 - "CompanionSnapshot"
Cohesion: 0.09
Nodes (21): 0014 - Discord Voice Companions Are Provider State With Visual Mapping, Consequences, Context, Decision, 0022 - Zoom Meeting Companions Use Provider Neutral Snapshots, Consequences, Context, Decision (+13 more)

### Community 32 - "BaseWeatherSource"
Cohesion: 0.15
Nodes (11): BaseWeatherSource, worker(), build_weather_source(), _list_value(), OpenMeteoWeatherSource, _openweathermap_to_wmo(), OpenWeatherMapWeatherSource, _optional_float() (+3 more)

### Community 33 - "overworld_scene.py"
Cohesion: 0.11
Nodes (13): day_night_palette(), DayNightPalette, MoodEngine, World, draw_house(), draw_lamp(), draw_tree(), make_tile() (+5 more)

### Community 35 - "crosshero.py"
Cohesion: 0.07
Nodes (28): _class_text(), _classes_from_payload(), CrossHeroClass, CrossHeroDaySource, CrossHeroWorkout, _dashboard_class_choices(), _dashboard_detail(), _dashboard_workout() (+20 more)

### Community 36 - "app.mjs"
Cohesion: 0.13
Nodes (25): animate(), ball(), base(), battle(), canvas, colors, ctx, demoStarted (+17 more)

### Community 37 - "draw_hud"
Cohesion: 0.12
Nodes (22): parse_hhmm(), status_for(), build_people_times(), PersonTime, _ai_mana_percent(), _ai_usage_percent(), _compact_hour_label(), _draw_flag() (+14 more)

### Community 38 - "datetime"
Cohesion: 0.10
Nodes (9): action(), execute(), AsyncCurrentSource, AsyncEventSource, AsyncPullRequestSource, run_background(), start(), _run_safely() (+1 more)

### Community 39 - "heltec-e213/src/main.cpp"
Cohesion: 0.14
Nodes (14): enterDeepSleep(), fetchWeather(), jsonNumber(), loop(), probeInternet(), probePcHealth(), saveWeatherCache(), serviceButton() (+6 more)

### Community 40 - "calendar.py"
Cohesion: 0.15
Nodes (23): _clean_ics_text(), _event_occurrences_between(), _first_url(), ics_events_between(), _ics_params(), _ics_person_label(), _ics_property_name(), _IcsEventComponent (+15 more)

### Community 41 - "eink_http.py"
Cohesion: 0.10
Nodes (6): compose_eink_white_background(), EInkDirtyRegion, EInkHttpOutput, encode_eink_frame(), find_eink_dirty_region(), EInkHttpOutputTests

### Community 42 - "SpaceshipEngine"
Cohesion: 0.13
Nodes (7): _asteroid_state(), _event_effect(), _fallback_event_key(), material_for_pr(), _pr_key(), SpaceshipEngine, RecordingScene

### Community 43 - "game"
Cohesion: 0.10
Nodes (20): game, ash_sprite_file, ash_sprite_source, ash_x, ash_y, encounter_x, fps, hud_height (+12 more)

### Community 44 - "LayoutPreview"
Cohesion: 0.16
Nodes (19): clampBox(), clampZoom(), defaultClockLayoutBox(), defaultEinkTelemetryLayoutBox(), defaultMediaAssetLayoutBox(), DisplayArrangement(), dragDisplayStart(), snapDisplay() (+11 more)

### Community 45 - "PixelOpsKiteHub"
Cohesion: 0.22
Nodes (7): hex(), hmacHex(), json(), parseJson(), PixelOpsKiteHub, unauthorized(), utf8()

### Community 46 - "esp32-c6-lcd-1.47/src/main.cpp"
Cohesion: 0.18
Nodes (11): authorized(), decodeHex(), drawMessage(), finishFrameUpload(), handleFrameUpload(), handleStatus(), loop(), renderFrame() (+3 more)

### Community 47 - "steps"
Cohesion: 0.11
Nodes (18): jobs, test, name, on, pull_request, push, branches, name (+10 more)

### Community 48 - "steps"
Cohesion: 0.11
Nodes (18): jobs, test, name, on, pull_request, push, branches, name (+10 more)

### Community 49 - "gamification.py"
Cohesion: 0.17
Nodes (10): 0024 - Gamification HUD Uses Provider-Neutral State, Consequences, Context, Decision, _event_finished(), GamificationSource, _hp_status(), _meeting_key() (+2 more)

### Community 50 - "google_calendar.py"
Cohesion: 0.14
Nodes (15): api_pages(), worker(), credential_lock(), credentials(), __call__(), _escape(), events_to_ics(), GoogleCalendarCache (+7 more)

### Community 51 - "discord/client.py"
Cohesion: 0.08
Nodes (24): ambient_signal_to_work_event(), AmbientProvider, AmbientSignal, AmbientSignalKind, classify_text_kind(), _event_shape(), classify_text_signal(), signal_to_work_event() (+16 more)

### Community 52 - "ThermalrightUsbTransport"
Cohesion: 0.20
Nodes (6): _device_selector_suffix(), _find_endpoint(), _find_interface(), _find_interface_for_endpoint(), hex_preview(), ThermalrightUsbTransport

### Community 53 - "datetime"
Cohesion: 0.13
Nodes (7): NullAIUsageSource, NullCompanionSource, NullMediaSource, NullPCStatsSource, NullPullRequestSource, NullTaskSource, NullWeatherSource

### Community 54 - "LocalMediaSource"
Cohesion: 0.08
Nodes (17): 0019 - Media Now Playing Is Local Presence, Consequences, Context, Decision, BrowserMediaSnapshotReceiver, do_POST(), _clean_lines(), _clean_youtube_title() (+9 more)

### Community 55 - "CalendarEventSource"
Cohesion: 0.27
Nodes (3): download_ics(), CalendarEventSource, worker()

### Community 56 - "SpaceshipScene"
Cohesion: 0.16
Nodes (4): SpaceshipSnapshot, _crew_position(), _diegetic_event_label(), SpaceshipScene

### Community 57 - "event_pokemon_types"
Cohesion: 0.12
Nodes (16): ai_usage, build_broken, deploy_completed, deploy_started, incident, meeting, merge, message_important (+8 more)

### Community 58 - "main"
Cohesion: 0.14
Nodes (21): CallableObservationSource, build_parser(), env_bool(), env_int(), env_value(), load_config(), load_display_config(), load_runtime_config() (+13 more)

### Community 59 - "main.cjs"
Cohesion: 0.23
Nodes (13): { app, BrowserWindow, Menu, Tray, nativeImage }, appRoot(), createRemoteWindow(), createTray(), createWindow(), http, npmCommand(), path (+5 more)

### Community 60 - "react"
Cohesion: 0.16
Nodes (8): DesktopMonitorPanel(), action(), Calendar, GoogleCalendarPanel(), run(), PixelMascot(), PixelMascotProps, react

### Community 61 - "codexAccount.ts"
Cohesion: 0.23
Nodes (4): CodexAccountBridge, localAccountRequest(), PythonAccountBridge, runtimeConfigApi()

### Community 62 - "handleHeartbeat"
Cohesion: 0.18
Nodes (15): authorized(), batteryStateName(), desiredRuntimeMode(), handleHeartbeat(), handleStatus(), hudBoxValue(), modeName(), resetReasonName() (+7 more)

### Community 63 - "vite.config.ts"
Cohesion: 0.05
Nodes (36): ConfigDescriptor, configStudioOrigin(), coreConfigFiles, DiscordGuildDescriptor, DiscordOAuthSession, discordOAuthSessions, discordRedirectUri(), DiscordTokenResponse (+28 more)

### Community 64 - "setup"
Cohesion: 0.20
Nodes (14): connectWifi(), deviceSuffix(), handleFrame(), loadPowerConfig(), loadStandaloneConfig(), parseHudBox(), persistLastDigest(), persistPowerConfig() (+6 more)

### Community 65 - "text_box.py"
Cohesion: 0.20
Nodes (13): draw_text_box(), _load_text_box_frame(), scroll_line_start(), _scroll_lines(), text_box_bottom_padding(), text_box_cursor_height(), text_box_layout(), text_box_line_height() (+5 more)

### Community 66 - "IntegrationPanel"
Cohesion: 0.08
Nodes (38): commaList(), CompanionSpriteRow(), csv(), Field(), firstLayoutWindowKey(), GithubIntegrationPanel(), connectWithToken(), poll() (+30 more)

### Community 67 - "DesktopManager"
Cohesion: 0.21
Nodes (3): DesktopManager, main(), DesktopTests

### Community 68 - "renderStandalone"
Cohesion: 0.15
Nodes (14): BatteryState, Charging, Critical, Discharging, Low, Stable, Unknown, batteryStateLabel() (+6 more)

### Community 69 - "test_lian_li_usb.py"
Cohesion: 0.18
Nodes (5): _command_packet(), _encode_jpeg(), LianLiUsbOutput, LianLiUsbTests, ReplyingTransport

### Community 70 - "SpaceshipStateStore"
Cohesion: 0.19
Nodes (4): _normalize_layout_seed(), _profile(), ShipProfile, SpaceshipStateStore

### Community 71 - "PokemonEngine"
Cohesion: 0.14
Nodes (6): merge_companion_snapshots(), PokemonEngine, PokemonEngineTests, RecordingEncounters, RecordingScene, engine()

### Community 72 - "adr/README.md"
Cohesion: 0.21
Nodes (5): 0039 — Kraken is a companion browser output, Consequences, Context, Architecture Decision Records, Windows tray and scheduled tasks

### Community 73 - "Pixel OPs Config Studio"
Cohesion: 0.29
Nodes (6): Build, E-ink firmware updates, Local API, Pixel OPs Config Studio, Run, What It Edits

### Community 74 - "encode_lcd_frame"
Cohesion: 0.18
Nodes (4): encode_lcd_frame(), LcdFrame, LcdHttpOutput, LcdHttpOutputTests

### Community 75 - "MovementAreaEditor"
Cohesion: 0.38
Nodes (11): clampMovementRect(), MovementAreaEditor(), addRect(), commit(), dragRect(), imagePoint(), resizeRect(), snap() (+3 more)

### Community 77 - "HudBox"
Cohesion: 0.20
Nodes (12): batteryPercent(), drawBatteryHud(), drawConfiguredTelemetryHuds(), drawHudFrame(), drawStatusHud(), drawWirelessHud(), HudBox, enabled (+4 more)

### Community 78 - "pixelops-kite/package.json"
Cohesion: 0.18
Nodes (11): devDependencies, wrangler@^4.0.0, name, private, scripts, deploy, dev, tail (+3 more)

### Community 79 - "people"
Cohesion: 0.17
Nodes (11): people, country, daylight_key, key, name, show_flag, standard_key, timezone (+3 more)

### Community 80 - "thermalright_cli.py"
Cohesion: 0.31
Nodes (4): build_thermalright_init_command(), build_thermalright_jpeg_packets(), encode_thermalright_jpeg(), ThermalrightJpegOptions

### Community 82 - "DiscordGatewayClient"
Cohesion: 0.08
Nodes (14): DiscordGatewayClient, beat(), DiscordCompanionProfile, DiscordCompanionStore, _int(), DiscordBusEventSource, DiscordIntegrationPlugin, plugin() (+6 more)

### Community 83 - "AmbientSignal"
Cohesion: 0.10
Nodes (21): _encode_meeting_id(), _find_participant(), _meeting_id(), _participant(), _participant_key(), _participant_signal(), _zoom_user_id(), ZoomApiClient (+13 more)

### Community 84 - "eslint.config.js"
Cohesion: 0.18
Nodes (10): @eslint/js@^9.32.0, eslint-plugin-react-hooks@^5.2.0, eslint-plugin-react-refresh@^0.4.20, globals@^15.15.0, typescript-eslint@^8.56.1, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh (+2 more)

### Community 85 - "manifest.json"
Cohesion: 0.18
Nodes (10): background, service_worker, type, content_scripts, description, host_permissions, manifest_version, name (+2 more)

### Community 86 - ".start"
Cohesion: 0.22
Nodes (8): _optional_bool(), ScreenControlServer, _body(), do_GET(), do_POST(), _send(), _unavailable(), test_loopback_control_selects_and_pins_a_screen()

### Community 87 - "WindowOutput"
Cohesion: 0.15
Nodes (5): enable_dpi_awareness(), hide_from_taskbar(), select_monitor(), WindowOutput, WindowOutputTests

### Community 88 - "Pixel OPs"
Cohesion: 0.12
Nodes (17): AI Decision Plugins, Architecture Records, Config Studio, Configuration, Credits, Extension Types, Game Engine Plugins, Hardware (+9 more)

### Community 89 - "account_hud.py"
Cohesion: 0.22
Nodes (14): draw_hardware(), paint(), draw_pr_activity(), paint(), draw_quota(), paint(), draw_status_strip(), meeting_column() (+6 more)

### Community 90 - "service-worker.js"
Cohesion: 0.29
Nodes (8): CROSSHERO_STUDIO_ENDPOINTS, postSnapshot(), providerForUrl(), publishBestSnapshot(), sanitize(), score(), selectBest(), snapshots

### Community 91 - "thermalright_usb.py"
Cohesion: 0.24
Nodes (12): _device_info(), _endpoint_direction(), _endpoint_type(), _find_usb_device(), _hex_or_dash(), _interfaces_for_device(), _log_device(), _safe_usb_string() (+4 more)

### Community 92 - "pokemon"
Cohesion: 0.22
Nodes (8): api_base_url, cache_dir, generation_limit, lazy_download, network_timeout_seconds, sprite_base_url, sprite_style, pokemon

### Community 93 - "PixelOpsApp"
Cohesion: 0.08
Nodes (12): 0026 - All Game Inputs Are Platform Events, Consequences, Context, Decision, 0029 - Screen Playlists Are Presentation State, Consequences, Context, Decision (+4 more)

### Community 94 - "BrowserView"
Cohesion: 0.12
Nodes (10): Decision, BrowserView, BrowserViewProvider, BrowserOutputServer, do_GET(), do_POST(), send_bytes(), setup() (+2 more)

### Community 95 - "WanderNavigator"
Cohesion: 0.23
Nodes (4): WanderNavigator, test_feet_can_follow_a_narrow_corridor_with_body_above_it(), test_routes_stay_on_the_connected_island_and_pause_when_disabled(), test_wandering_crosses_joined_rectangles_without_entering_obstacle()

### Community 96 - "throttle"
Cohesion: 0.25
Nodes (8): throttle, cooldown_seconds, enabled, max_pending, max_requests_per_window, skip_categories, skip_sources, window_seconds

### Community 97 - "events"
Cohesion: 0.25
Nodes (8): knowledge_path, mock_events, queue_limit, repo_biomes, events, backend, frontend, infra

### Community 98 - "0032 - Waveshare Bluetooth frame transport"
Cohesion: 0.29
Nodes (6): 0032 - Waveshare Bluetooth frame transport, Consequences, Context, Decision, macOS reconnect lifecycle, Partial updates (BLE v2)

### Community 99 - "json"
Cohesion: 0.23
Nodes (10): resolve_executable(), test_boot_path_can_find_the_installed_native_codex_without_injected_path(), advance(), observation(), test_a_long_capture_is_not_cut_off_at_the_meeting_boundary(), test_intro_countdown_then_pr_battle_on_both_views(), test_outro_and_next_intro_give_fifteen_uninterrupted_thermal_seconds(), test_private_meetings_events_and_unknown_repository_identities_are_not_projected() (+2 more)

### Community 100 - "encounter"
Cohesion: 0.29
Nodes (7): appears_seconds, caught_seconds, shake_seconds, start_seconds, throw_seconds, walking_seconds, encounter

### Community 101 - "content-script.js"
Cohesion: 0.62
Nodes (6): channelName(), cleanText(), cleanTitle(), publish(), readMediaState(), sourceName()

### Community 102 - "ADR 0008: CrossHero fitness data enters as a daily observation"
Cohesion: 0.33
Nodes (5): ADR 0008: CrossHero fitness data enters as a daily observation, Consequences, Context, Decision, Status

### Community 103 - "ADR 0025: E-ink displays are hybrid network outputs"
Cohesion: 0.33
Nodes (5): ADR 0025: E-ink displays are hybrid network outputs, Consequences, Context, Decision, Status

### Community 104 - "ADR 0026: Color LCDs are network output terminals"
Cohesion: 0.33
Nodes (5): ADR 0026: Color LCDs are network output terminals, Consequences, Context, Decision, Status

### Community 105 - "PokemonKnowledge"
Cohesion: 0.22
Nodes (3): PokemonKnowledge, PokemonKnowledgeBase, _env_bool()

### Community 106 - "0009 - Meetings Are Ambient Ceremonies"
Cohesion: 0.40
Nodes (4): 0009 - Meetings Are Ambient Ceremonies, Consequences, Context, Decision

### Community 107 - "Pixel OPs — Heltec Vision Master E213"
Cohesion: 0.33
Nodes (5): Energia e diagnóstico, Gravar, Modos autônomos, Pixel OPs — Heltec Vision Master E213, Protocolo

### Community 109 - "0001 - Ambient Social Observability, Not Feeds"
Cohesion: 0.40
Nodes (4): 0001 - Ambient Social Observability, Not Feeds, Consequences, Context, Decision

### Community 110 - "0037 - PR inventory is not a new arrival"
Cohesion: 0.40
Nodes (4): 0037 - PR inventory is not a new arrival, Consequences, Context, Decision

### Community 111 - "ThermalrightProtocol"
Cohesion: 0.16
Nodes (4): FrameBufferOptions, split_frame_chunks(), ThermalrightPlugin, ThermalrightProtocol

### Community 113 - "0006 - Secrets Stay In Env, Runtime Toggles Move To JSON"
Cohesion: 0.40
Nodes (4): 0006 - Secrets Stay In Env, Runtime Toggles Move To JSON, Consequences, Context, Decision

### Community 114 - "0007 - AI Decisions Are Optional, Cached, And Throttled"
Cohesion: 0.40
Nodes (4): 0007 - AI Decisions Are Optional, Cached, And Throttled, Consequences, Context, Decision

### Community 115 - "0020 - Tasks HUDs Share Provider-Neutral Board State"
Cohesion: 0.33
Nodes (5): 0020 - Tasks HUDs Share Provider-Neutral Board State, Consequences, Context, Decision, Status

### Community 116 - "split_map_sheets.py"
Cohesion: 0.38
Nodes (6): component_is_map(), connected_components(), is_background(), main(), slugify(), split_sheet()

### Community 117 - "Pokemon Plugin"
Cohesion: 0.12
Nodes (16): Calendar Events, Common Recipes, Credits, Display Config, Game Config, GitHub Events, Main Config Files, Maps (+8 more)

### Community 118 - "0013 - Config Studio Discovers Plugin-Owned Config"
Cohesion: 0.40
Nodes (4): 0013 - Config Studio Discovers Plugin-Owned Config, Consequences, Context, Decision

### Community 119 - "0015 - Timezone Config Is Derived From IANA Selection"
Cohesion: 0.40
Nodes (4): 0015 - Timezone Config Is Derived From IANA Selection, Consequences, Context, Decision

### Community 120 - "0016 - PC Stats Are Local Integration Metrics"
Cohesion: 0.40
Nodes (4): 0016 - PC Stats Are Local Integration Metrics, Consequences, Context, Decision

### Community 121 - "0017 - Linux And Windows Are Supported Runtime Targets"
Cohesion: 0.40
Nodes (4): 0017 - Linux And Windows Are Supported Runtime Targets, Consequences, Context, Decision

### Community 123 - "0021 - Local Runtime State Uses SQLite"
Cohesion: 0.40
Nodes (4): 0021 - Local Runtime State Uses SQLite, Consequences, Context, Decision

### Community 124 - "ClickUpTaskSource"
Cohesion: 0.36
Nodes (3): ClickUpTaskSource, _ids_from_config(), ClickUpTaskSourceTests

### Community 125 - "0027 - Spaceship Progress Is Active-Time And Game-Owned"
Cohesion: 0.40
Nodes (4): 0027 - Spaceship Progress Is Active-Time And Game-Owned, Consequences, Context, Decision

### Community 126 - "CalendarController"
Cohesion: 0.30
Nodes (7): CalendarController, authorization_url(), fetch_token(), main(), test_client_import_is_sanitized_and_rejects_non_google_endpoints(), test_real_loopback_signin_uses_pkce_and_cancel_releases_the_profile_without_tokens(), test_successful_login_persists_credentials_without_returning_them_to_studio()

### Community 127 - "0031 - Waveshare LCD supports USB frame delivery"
Cohesion: 0.40
Nodes (4): 0031 - Waveshare LCD supports USB frame delivery, Consequences, Context, Decision

### Community 128 - "Pixel OPs firmware for ESP32-C6-LCD-1.47"
Cohesion: 0.40
Nodes (4): Atualizar dados por Bluetooth, Atualizar dados por USB, Build and upload, Pixel OPs firmware for ESP32-C6-LCD-1.47

### Community 129 - "ai_selector"
Cohesion: 0.40
Nodes (5): ambient, async, candidate_limit, enabled, ai_selector

### Community 130 - "Pixel OPs Browser Bridge Extension"
Cohesion: 0.40
Nodes (4): CrossHero session, Data sent, Install, Pixel OPs Browser Bridge Extension

### Community 131 - "CalendarEvent"
Cohesion: 0.14
Nodes (13): CalendarEvent, upcoming_strip_meetings(), _activity_label(), _draw_meeting_card(), _meeting_duration_label(), _meeting_location_label(), _meeting_meta_lines(), _meeting_people_label() (+5 more)

### Community 132 - "Windows Setup"
Cohesion: 0.25
Nodes (7): Config Studio, Output Tests, PC Stats Notes, Python Environment, System Requirements, TURZX USB Display, Windows Setup

### Community 133 - "integration_plugins/registry.py"
Cohesion: 0.19
Nodes (7): build_integration_runtime(), IntegrationRuntime, _load_plugin(), _merge(), _selected_plugin_names(), context(), IntegrationPluginTests

### Community 134 - "Google Calendar account setup"
Cohesion: 0.40
Nodes (4): Connect locally, Create the client, Google Calendar account setup, Storage and lifecycle

### Community 135 - "Spaceship game"
Cohesion: 0.40
Nodes (4): Assets, Persistence, Procedural layout, Spaceship game

### Community 136 - "PixelOpsKite"
Cohesion: 0.50
Nodes (3): Deploy, Endpoints, PixelOpsKite

### Community 137 - "walk"
Cohesion: 0.67
Nodes (3): listPokemonMaps(), walk(), pngDimensions()

### Community 138 - "StandalonePage"
Cohesion: 0.67
Nodes (3): StandalonePage, Diagnostics, Summary

### Community 139 - "DiscordIntegrationPanel"
Cohesion: 0.18
Nodes (14): clampNumber(), digits(), DiscordIntegrationPanel(), connectWithBotToken(), loadServers(), poll(), refreshProfile(), startLogin() (+6 more)

### Community 140 - "GitHubEventSource"
Cohesion: 0.12
Nodes (7): _env_bool(), GitHubEventSource, decode(), worker(), PullRequestSummary, GitHubEventSourceTests, request()

### Community 144 - "0002 - Provider Integrations Are Runtime Plugins"
Cohesion: 0.40
Nodes (4): 0002 - Provider Integrations Are Runtime Plugins, Consequences, Context, Decision

### Community 146 - "TaskSnapshot"
Cohesion: 0.31
Nodes (4): MergedTaskSource, _task_sort_key(), TaskSnapshot, TaskSource

### Community 148 - "emoji_image"
Cohesion: 0.26
Nodes (8): canvas_font_scale(), emoji_image(), icon_font(), _load_font(), _macos_emoji_image(), _pillow_emoji_image(), _scaled_font_size(), _draw_temperature_range()

### Community 150 - "DisplayOutput"
Cohesion: 0.09
Nodes (4): DisplayOutput, _HealthHandler, _PullFrameHandler, GifOutput

### Community 154 - "Thermalright USB Plugin"
Cohesion: 0.20
Nodes (9): Capturing More Data, CLI, Current Python API, Future Work, Known Observations, Pixel OPs Output, Replay Format, Safety Model (+1 more)

### Community 156 - "Linux Setup"
Cohesion: 0.29
Nodes (6): Linux Setup, Output Tests, PC Stats Notes, Python Environment, System Packages, TURZX USB Display

### Community 161 - "os"
Cohesion: 0.21
Nodes (6): _due_datetime(), _ids_from_config(), _task_from_payload(), _task_sort_key(), TodoistTaskSource, TodoistTaskSourceTests

### Community 167 - "splash.py"
Cohesion: 0.25
Nodes (7): _contain_resize(), _draw_pixel_grid(), _logo_path(), render_splash(), splash_frame_count(), splash_seconds(), SplashTests

### Community 175 - "inspect_packet"
Cohesion: 0.19
Nodes (7): inspect_packet(), parse_image_chunk_header(), _parse_int(), _parse_usbpcap_frame(), _possible_command(), _replay_packet_from_json(), ThermalrightImageChunkInfo

### Community 178 - "0004 - Slack Uses Socket Mode Only"
Cohesion: 0.40
Nodes (4): 0004 - Slack Uses Socket Mode Only, Consequences, Context, Decision

### Community 180 - "test_core.py"
Cohesion: 0.07
Nodes (14): config_path(), ConfigWatcher, load_config(), load_config_prefer_json(), runtime_plugin_name(), CoreTests, DummyAiUsage, DummyCompanionSource (+6 more)

### Community 181 - "build"
Cohesion: 0.13
Nodes (15): build, appId, asar, extraResources, files, linux, nsis, productName (+7 more)

### Community 187 - "ProjectSnapshot"
Cohesion: 0.08
Nodes (43): State, ADR 0028: Project Radar Uses Provider-Neutral Observations, Consequences, Context, Decision, Status, CapacitiesProjectSource, _definition_map() (+35 more)

### Community 188 - "lian_li_usb.py"
Cohesion: 0.14
Nodes (8): set_border_color(), _bind(), _device_path(), _device_paths(), _led_ring_path(), LianLiWinUsb, _open_error(), scan_lian_li_serials()

### Community 191 - "test_codex_status.py"
Cohesion: 0.10
Nodes (12): 0030 - Codex activity is a neutral observation, Consequences, Context, Decision, Per-task HUD, Status, AIActivitySnapshot, AIActivityTask (+4 more)

### Community 192 - "_PullFrameServer"
Cohesion: 0.20
Nodes (3): EInkFrame, _PullFrameServer, _PullFrameState

### Community 193 - "0011 - Graphify Artifacts Document The Codebase Map"
Cohesion: 0.40
Nodes (4): 0011 - Graphify Artifacts Document The Codebase Map, Consequences, Context, Decision

### Community 194 - "TURZXOutput"
Cohesion: 0.18
Nodes (4): _optional_int(), _parse_int(), TURZXOutput, TurzxOutputTests

### Community 195 - "argparse"
Cohesion: 0.24
Nodes (8): build_parser(), clean_frame(), close_color(), crop_strip(), main(), parse_box(), write_manifest(), main()

### Community 196 - "0036 - Windows desktop lifecycle is per-user"
Cohesion: 0.40
Nodes (4): 0036 - Windows desktop lifecycle is per-user, Consequences, Context, Decision

### Community 197 - "desktop.py"
Cohesion: 0.25
Nodes (3): run_tray(), setup(), watch()

### Community 200 - "next_event"
Cohesion: 0.32
Nodes (6): next_mock_event(), load_env(), cached_next_event(), cached_today_events(), next_event(), today_events()

### Community 201 - "startFirmwareOperation"
Cohesion: 0.60
Nodes (5): discoverFirmwarePorts(), firmwareStatus(), pushFirmwareLog(), resolvePlatformioCommand(), startFirmwareOperation()

### Community 202 - "0038 - Google Calendar uses read-only user OAuth"
Cohesion: 0.40
Nodes (4): 0038 - Google Calendar uses read-only user OAuth, Consequences, Context, Decision

### Community 205 - "dataclasses"
Cohesion: 0.12
Nodes (10): EventPriority, ceremony_for_title(), MeetingCeremony, MeetingCeremonyType, work_event_for_meeting(), _env_bool(), repo_types(), time_types() (+2 more)

### Community 206 - "scripts"
Cohesion: 0.18
Nodes (11): scripts, app:build, app:build:linux, app:build:mac, app:build:win, app:dev, build, dev (+3 more)

### Community 207 - "0005 - JSON Runtime Configuration And Hot Reload"
Cohesion: 0.40
Nodes (4): 0005 - JSON Runtime Configuration And Hot Reload, Consequences, Context, Decision

### Community 208 - "ShowOffScenario"
Cohesion: 0.20
Nodes (5): 0040 — Show off is an isolated game projection, Consequences, Context, Decision, ShowOffScenario

### Community 209 - "0023 - PixelOpsKite Relays Webhooks Over WebSocket"
Cohesion: 0.40
Nodes (4): 0023 - PixelOpsKite Relays Webhooks Over WebSocket, Consequences, Context, Decision

### Community 210 - "0034 - Account quota is a neutral observation"
Cohesion: 0.40
Nodes (4): 0034 - Account quota is a neutral observation, Consequences, Context, Decision

### Community 212 - "0033 — Token history HUD"
Cohesion: 0.50
Nodes (3): 0033 — Token history HUD, Consequences, Decision

### Community 213 - "0018 - ClickUp Tasks Are Planning Snapshots"
Cohesion: 0.40
Nodes (4): 0018 - ClickUp Tasks Are Planning Snapshots, Consequences, Context, Decision

### Community 214 - "0008 - Pokemon Is A Visual Plugin, Not The Integration Model"
Cohesion: 0.50
Nodes (4): 0008 - Pokemon Is A Visual Plugin, Not The Integration Model, Consequences, Context, Decision

### Community 215 - "0041 - Lian Li native USB output"
Cohesion: 0.40
Nodes (4): 0041 - Lian Li native USB output, Consequences, Context, Decision

### Community 216 - "ai_usage.py"
Cohesion: 0.10
Nodes (32): 0012 - AI Usage Becomes Ambient Gauges And Events, Consequences, Context, Decision, _active_codex_limit_percent(), AIUsageGauge, AIUsageSource, _aware() (+24 more)

### Community 218 - "config-studio/package.json"
Cohesion: 0.13
Nodes (19): dependencies, lucide-react@^0.575.0, react@^19.2.0, react-dom@^19.2.0, typescript@^5.8.3, vite@^7.3.1, @vitejs/plugin-react@^5.0.4, engines (+11 more)

### Community 219 - "ScreenRotationController"
Cohesion: 0.22
Nodes (11): _iso(), _parse_config(), ScreenPresentation, ScreenRotationController, _utc(), _config(), test_legacy_layout_becomes_non_rotating_default_screen(), test_manual_selection_pins_until_rotation_is_resumed() (+3 more)

### Community 220 - "0010 - Weather, Calendar, GitHub, Slack, Discord Share The Same Runtime Boundary"
Cohesion: 0.50
Nodes (4): 0010 - Weather, Calendar, GitHub, Slack, Discord Share The Same Runtime Boundary, Consequences, Context, Decision

### Community 231 - "discoverRuntimeProcess"
Cohesion: 0.15
Nodes (21): discoverRuntimeProcess(), friendlyUsbError(), identifyThermalrightDisplay(), isPixelOpsRuntimeCommand(), isProcessAlive(), processCommand(), pushRuntimeLog(), removeRuntimePid() (+13 more)

### Community 239 - "installRuntimeAutostart"
Cohesion: 0.22
Nodes (16): autostartPaths(), ensureRuntimeLaunchers(), execFileAsync, fileExists(), installRuntimeAutostart(), macAutostartLogDir(), macAutostartSupportDir(), macLaunchAgentDomain() (+8 more)

### Community 326 - "main.py"
Cohesion: 0.16
Nodes (28): _args_selects_output(), build_output(), _configured_display_for_output(), _display_region_size(), _display_runtime_config(), _layout_for_display(), build_runtime_targets(), _mark_eink_layout_regions() (+20 more)

### Community 537 - "font"
Cohesion: 0.17
Nodes (43): CrossHeroDaySnapshot, GamificationSnapshot, font(), _clock_skin_color(), _draw_activity_panel(), _draw_ai_usage_panel(), _draw_analog_clock(), _draw_clock_hand() (+35 more)

### Community 551 - "readDotEnv"
Cohesion: 0.17
Nodes (13): completeDiscordOAuth(), discordProfileFromToken(), discordToken(), envValue(), githubToken(), kiteStatus(), listGithubRepos(), loadDiscordProfile() (+5 more)

### Community 613 - "detectVisualPlugins"
Cohesion: 0.27
Nodes (12): buildConfigManifest(), configDescriptorsFor(), detectIntegrationPlugins(), detectVisualPlugins(), listDirectories(), loadRuntimeConfig(), pathExists(), pluginConfigKey() (+4 more)

### Community 743 - "runKiteCommand"
Cohesion: 0.28
Nodes (9): configureKiteSecrets(), kiteDeploy(), kiteInstall(), kitePutSecret(), kiteUrlsFromOutput(), npmCommand(), npxCommand(), runKiteCommand() (+1 more)

### Community 761 - "PixelOpsStateStore"
Cohesion: 0.17
Nodes (12): _datetime_iso(), _discord_person_from_row(), DiscordPersonRecord, _json(), _layout_profile_from_row(), LayoutProfileRecord, _loads(), _now_iso() (+4 more)

### Community 778 - "LcdBleOutput"
Cohesion: 0.10
Nodes (10): bluetooth_loop(), changed_region(), LcdBleOutput, pack_frame(), BleDeliveryTests, write(), BleEncodingTests, BluetoothLoopLifetimeTests (+2 more)

### Community 811 - "mac"
Cohesion: 0.50
Nodes (4): mac, NSBluetoothAlwaysUsageDescription, extendInfo, target

## Knowledge Gaps
- **38 isolated node(s):** `SERVICE`, `COMMAND`, `DATA`, `STATUS`, `INFO` (+33 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 965 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **49 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `State` connect `ProjectSnapshot` to `react`?**
  _High betweenness centrality (0.232) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `OverworldScene` (e.g. with `PokemonEngine` and `PokemonPlugin`) actually correct?**
  _`OverworldScene` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `SERVICE`, `COMMAND`, `DATA` to the rest of the system?**
  _38 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `IntegrationContext` be split into smaller, more focused modules?**
  _Cohesion score 0.07890137328339576 - nodes in this community are weakly interconnected._
- **Why does `WorkEvent` connect `WorkEvent` to `IntegrationContext`, `PokemonAiPromptBuilder`, `AIUsageSnapshot`, `test_spaceship.py`, `GitHubEventSource`, `hud.py`, `OverworldScene`, `EventCategory`, `SlackAmbientAggregator`, `font`, `test_pr_arrivals.py`, `PixelOpsEvent`, `VisualAndAiPluginTests`, `overworld_scene.py`, `draw_hud`, `SpaceshipEngine`, `discord/client.py`, `CalendarEventSource`, `SpaceshipScene`, `ProjectSnapshot`, `PokemonEngine`, `dataclasses`, `ShowOffScenario`, `0023 - PixelOpsKite Relays Webhooks Over WebSocket`, `0008 - Pokemon Is A Visual Plugin, Not The Integration Model`, `ai_usage.py`, `Pixel OPs`, `PixelOpsApp`, `json`, `PokemonKnowledge`, `0027 - Spaceship Progress Is Active-Time And Game-Owned`?**
  _High betweenness centrality (0.172) - this node is a cross-community bridge._
- **Are the 44 inferred relationships involving `WorkEvent` (e.g. with `Architecture` and `Integration Plugins`) actually correct?**
  _`WorkEvent` has 44 INFERRED edges - model-reasoned connections that need verification._
- **Should `App.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.05224963715529753 - nodes in this community are weakly interconnected._