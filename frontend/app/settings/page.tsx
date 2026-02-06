"use client";

import { useState, useEffect } from "react";
import {
    Container,
    Paper,
    Title,
    Text,
    NumberInput,
    Switch,
    Button,
    Stack,
    Group,
    Badge,
    Loader,
    Center,
    Alert,
    Divider,
} from "@mantine/core";
import { IconSettings, IconDatabase, IconRefresh, IconCheck, IconTrash } from "@tabler/icons-react";

interface VectorStoreInfo {
    collection_count: number;
    embedding_model: string;
}

interface Settings {
    temperature: number;
    citation_required: boolean;
    unanswerable_guard: boolean;
    confliction_detection: boolean;
}

export default function SettingsPage() {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [vectorInfo, setVectorInfo] = useState<VectorStoreInfo | null>(null);
    const [settings, setSettings] = useState<Settings>({
        temperature: 0.3,
        citation_required: true,
        unanswerable_guard: true,
        confliction_detection: true,
    });
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        Promise.all([fetchVectorInfo(), fetchSettings()]).finally(() => setLoading(false));
    }, []);

    const fetchVectorInfo = async () => {
        try {
            const res = await fetch("http://localhost:8000/api/feedbacks/stats");
            if (res.ok) {
                const data = await res.json();
                setVectorInfo({
                    collection_count: data.total || 0,
                    embedding_model: "all-MiniLM-L6-v2",
                });
            }
        } catch (e) {
            console.error("Failed to fetch vector info:", e);
        }
    };

    const fetchSettings = async () => {
        try {
            const res = await fetch("http://localhost:8000/api/settings/");
            if (res.ok) {
                const data = await res.json();
                setSettings({
                    temperature: data.temperature ?? 0.3,
                    citation_required: data.citation_required ?? true,
                    unanswerable_guard: data.unanswerable_guard ?? true,
                    confliction_detection: data.confliction_detection ?? true,
                });
            }
        } catch (e) {
            console.error("Failed to fetch settings:", e);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        setError(null);
        try {
            const res = await fetch("http://localhost:8000/api/settings/", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(settings),
            });

            if (res.ok) {
                setSaved(true);
                setTimeout(() => setSaved(false), 3000);
            } else {
                setError("Fehler beim Speichern");
            }
        } catch (e) {
            setError("Verbindung zum Backend fehlgeschlagen");
        } finally {
            setSaving(false);
        }
    };

    const handleReset = async () => {
        if (confirm("Wirklich alle Einstellungen zurücksetzen?")) {
            try {
                const res = await fetch("http://localhost:8000/api/settings/reset", {
                    method: "POST",
                });
                if (res.ok) {
                    const data = await res.json();
                    setSettings(data.settings);
                    setSaved(true);
                    setTimeout(() => setSaved(false), 3000);
                }
            } catch (e) {
                setError("Fehler beim Zurücksetzen");
            }
        }
    };

    if (loading) {
        return (
            <Center h="50vh">
                <Loader size="lg" />
            </Center>
        );
    }

    return (
        <Container size="md">
            <Group justify="space-between" mb="lg">
                <Title order={2}>⚙️ Einstellungen</Title>
                {saved && (
                    <Badge color="green" size="lg" leftSection={<IconCheck size={14} />}>
                        Gespeichert
                    </Badge>
                )}
            </Group>

            {error && (
                <Alert color="red" mb="md" onClose={() => setError(null)} withCloseButton>
                    {error}
                </Alert>
            )}

            <Stack gap="lg">
                {/* RAG-Konfiguration */}
                <Paper withBorder p="lg" radius="md">
                    <Group mb="md">
                        <IconSettings size={24} color="var(--mantine-color-blue-6)" />
                        <Text fw={500}>RAG-Konfiguration</Text>
                    </Group>

                    <Stack gap="md">
                        <NumberInput
                            label="LLM Temperatur"
                            description="Niedrig (0.0-0.3) = präziser, Hoch (0.7-1.0) = kreativer"
                            value={settings.temperature}
                            onChange={(val) =>
                                setSettings({ ...settings, temperature: typeof val === "number" ? val : 0.3 })
                            }
                            min={0}
                            max={1}
                            step={0.1}
                            decimalScale={1}
                        />

                        <Text size="sm" c="dimmed">
                            API-Key und Modell werden über Umgebungsvariablen konfiguriert (.env)
                        </Text>
                    </Stack>
                </Paper>

                {/* VectorStore */}
                <Paper withBorder p="lg" radius="md">
                    <Group mb="md" justify="space-between">
                        <Group>
                            <IconDatabase size={24} color="var(--mantine-color-green-6)" />
                            <Text fw={500}>VectorStore Status</Text>
                        </Group>
                        <Badge color="green">Verbunden</Badge>
                    </Group>

                    <Stack gap="md">
                        <Group justify="space-between">
                            <Text size="sm">Dokumente im Index</Text>
                            <Text fw={500}>{vectorInfo?.collection_count?.toLocaleString() ?? 0}</Text>
                        </Group>
                        <Group justify="space-between">
                            <Text size="sm">Embedding-Modell</Text>
                            <Text fw={500}>{vectorInfo?.embedding_model ?? "all-MiniLM-L6-v2"}</Text>
                        </Group>
                        <Group justify="space-between">
                            <Text size="sm">Retrieval-Methode</Text>
                            <Badge variant="light" color="blue">Hybrid (BM25 + Vector)</Badge>
                        </Group>

                        <Divider my="xs" />

                        <Button
                            variant="light"
                            color="blue"
                            leftSection={<IconRefresh size={16} />}
                            onClick={fetchVectorInfo}
                        >
                            Status aktualisieren
                        </Button>
                    </Stack>
                </Paper>

                {/* Guardrails */}
                <Paper withBorder p="lg" radius="md">
                    <Group mb="md">
                        <IconSettings size={24} color="var(--mantine-color-orange-6)" />
                        <Text fw={500}>Guardrails</Text>
                        <Badge size="sm" color="orange">Literatur: Wu & Wu (2025)</Badge>
                    </Group>

                    <Stack gap="md">
                        <Switch
                            label="Zitationspflicht"
                            description="Jede Aussage muss mit Quellen belegt werden [Q1], [Q2]..."
                            checked={settings.citation_required}
                            onChange={(e) =>
                                setSettings({ ...settings, citation_required: e.target.checked })
                            }
                        />
                        <Switch
                            label="Unanswerable Guard"
                            description="'Keine Information verfügbar' wenn keine passenden Quellen"
                            checked={settings.unanswerable_guard}
                            onChange={(e) =>
                                setSettings({ ...settings, unanswerable_guard: e.target.checked })
                            }
                        />
                        <Switch
                            label="Confliction Detection"
                            description="Widersprüchliche Quellen erkennen (experimentell)"
                            checked={settings.confliction_detection}
                            onChange={(e) =>
                                setSettings({ ...settings, confliction_detection: e.target.checked })
                            }
                        />
                    </Stack>
                </Paper>

                {/* Aktionen */}
                <Group justify="space-between">
                    <Button
                        variant="subtle"
                        color="red"
                        leftSection={<IconTrash size={16} />}
                        onClick={handleReset}
                    >
                        Zurücksetzen
                    </Button>
                    <Button loading={saving} onClick={handleSave}>
                        Einstellungen speichern
                    </Button>
                </Group>
            </Stack>
        </Container>
    );
}
