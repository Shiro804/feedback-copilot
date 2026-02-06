"use client";

import { useState } from "react";
import {
    Container,
    Paper,
    Title,
    Text,
    Group,
    Button,
    Stack,
    FileInput,
    Progress,
    Alert,
    Badge,
    Table,
    ScrollArea,
    Code,
} from "@mantine/core";
import {
    IconUpload,
    IconCheck,
    IconAlertTriangle,
    IconShield,
    IconDatabase,
    IconCar,
} from "@tabler/icons-react";

interface PIIMatch {
    type: string;
    text: string;
    start: number;
    end: number;
}

interface UploadStats {
    by_label?: Record<string, number>;
    by_model?: Record<string, number>;
    by_market?: Record<string, number>;
    by_source?: Record<string, number>;
}

export default function IngestPage() {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [piiMatches, setPiiMatches] = useState<PIIMatch[]>([]);
    const [result, setResult] = useState<{
        success: boolean;
        processed: number;
        stats?: UploadStats;
    } | null>(null);

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setProgress(0);
        setPiiMatches([]);
        setResult(null);

        const interval = setInterval(() => {
            setProgress((prev) => {
                if (prev >= 90) return 90;
                return prev + 10;
            });
        }, 200);

        try {
            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch("http://localhost:8000/api/ingest/upload", {
                method: "POST",
                body: formData,
            });

            clearInterval(interval);
            setProgress(100);

            if (response.ok) {
                const data = await response.json();

                if (data.pii_detected && data.pii_detected.length > 0) {
                    setPiiMatches(data.pii_detected);
                }

                setResult({
                    success: true,
                    processed: data.processed || 0,
                    stats: data.stats
                });
            } else {
                const error = await response.json();
                setResult({ success: false, processed: 0 });
                console.error("Upload-Fehler:", error);
            }
        } catch (error) {
            clearInterval(interval);
            console.error("Upload fehlgeschlagen:", error);
            setResult({ success: false, processed: 0 });
        } finally {
            setUploading(false);
        }
    };

    const piiTypeColors: Record<string, string> = {
        email: "blue",
        phone_de: "green",
        plate_de: "orange",
        vin: "red",
        person: "violet",
        PERSON: "violet",
        LOC: "cyan",
        GPE: "teal",
        ORG: "indigo",
    };

    return (
        <Container size="lg">
            <Title order={2} mb="lg">
                📥 Feedback-Import
            </Title>

            <Stack gap="lg">
                {/* Info-Box mit VW-spezifischen Feldern */}
                <Alert icon={<IconCar size={16} />} color="blue" variant="light">
                    <Text fw={500} mb="xs">VW-Feedback Datenformat</Text>
                    <Text size="sm">
                        <strong>Pflichtfelder:</strong>{" "}
                        <Code>text</Code>, <Code>label</Code> (Kategorie)
                    </Text>
                    <Text size="sm" mt="xs">
                        <strong>VW-spezifisch:</strong>{" "}
                        <Code>vehicle_model</Code> (ID.4, Golf 8...),{" "}
                        <Code>market</Code> (DE, US, UK...),{" "}
                        <Code>source_type</Code> (voice, touch, error)
                    </Text>
                    <Text size="sm" mt="xs" c="dimmed">
                        Unterstützte Formate: JSONL, JSON, CSV
                    </Text>
                </Alert>

                {/* Upload-Bereich */}
                <Paper withBorder p="lg" radius="md">
                    <Group align="flex-start" gap="lg">
                        <IconUpload size={48} color="var(--mantine-color-blue-6)" />
                        <div style={{ flex: 1 }}>
                            <Text fw={500} mb="xs">
                                Feedback-Datei hochladen
                            </Text>
                            <Text size="sm" c="dimmed" mb="md">
                                PII wird automatisch erkannt und anonymisiert (spaCy NER + Regex).
                            </Text>

                            <Group>
                                <FileInput
                                    placeholder="Datei auswählen..."
                                    value={file}
                                    onChange={setFile}
                                    accept=".csv,.json,.jsonl"
                                    style={{ flex: 1 }}
                                />
                                <Button
                                    onClick={handleUpload}
                                    loading={uploading}
                                    disabled={!file}
                                    leftSection={<IconUpload size={16} />}
                                >
                                    Hochladen
                                </Button>
                            </Group>

                            {uploading && (
                                <Progress value={progress} mt="md" animated />
                            )}
                        </div>
                    </Group>
                </Paper>

                {/* Import Stats - VW-spezifisch */}
                {result?.success && result.stats && (
                    <Paper withBorder p="lg" radius="md">
                        <Group mb="md">
                            <IconDatabase size={24} color="var(--mantine-color-teal-6)" />
                            <Text fw={500}>Import-Statistiken</Text>
                        </Group>

                        <Group gap="xl" wrap="wrap">
                            {result.stats.by_label && Object.keys(result.stats.by_label).length > 0 && (
                                <div>
                                    <Text size="sm" c="dimmed" mb="xs">Kategorien:</Text>
                                    <Group gap="xs">
                                        {Object.entries(result.stats.by_label).slice(0, 5).map(([label, count]) => (
                                            <Badge key={label} variant="light" color="blue">
                                                {label}: {count}
                                            </Badge>
                                        ))}
                                    </Group>
                                </div>
                            )}
                            {result.stats.by_model && Object.keys(result.stats.by_model).length > 0 && (
                                <div>
                                    <Text size="sm" c="dimmed" mb="xs">Fahrzeugmodelle:</Text>
                                    <Group gap="xs">
                                        {Object.entries(result.stats.by_model).slice(0, 5).map(([model, count]) => (
                                            <Badge key={model} variant="light" color="violet">
                                                {model}: {count}
                                            </Badge>
                                        ))}
                                    </Group>
                                </div>
                            )}
                            {result.stats.by_market && Object.keys(result.stats.by_market).length > 0 && (
                                <div>
                                    <Text size="sm" c="dimmed" mb="xs">Märkte:</Text>
                                    <Group gap="xs">
                                        {Object.entries(result.stats.by_market).slice(0, 5).map(([market, count]) => (
                                            <Badge key={market} variant="light" color="teal">
                                                {market}: {count}
                                            </Badge>
                                        ))}
                                    </Group>
                                </div>
                            )}
                            {result.stats.by_source && Object.keys(result.stats.by_source).length > 0 && (
                                <div>
                                    <Text size="sm" c="dimmed" mb="xs">Quellen:</Text>
                                    <Group gap="xs">
                                        {Object.entries(result.stats.by_source).map(([source, count]) => (
                                            <Badge key={source} variant="light" color="orange">
                                                {source}: {count}
                                            </Badge>
                                        ))}
                                    </Group>
                                </div>
                            )}
                        </Group>
                    </Paper>
                )}

                {/* PII-Preview */}
                {piiMatches.length > 0 && (
                    <Paper withBorder p="lg" radius="md">
                        <Group mb="md">
                            <IconShield size={24} color="var(--mantine-color-orange-6)" />
                            <Text fw={500}>PII-Erkennung (spaCy NER + Regex)</Text>
                            <Badge color="orange">{piiMatches.length} gefunden</Badge>
                        </Group>

                        <Text size="sm" c="dimmed" mb="md">
                            Personenbezogene Daten wurden erkannt und anonymisiert.
                        </Text>

                        <ScrollArea>
                            <Table striped>
                                <Table.Thead>
                                    <Table.Tr>
                                        <Table.Th>Typ</Table.Th>
                                        <Table.Th>Gefunden</Table.Th>
                                        <Table.Th>Anonymisiert zu</Table.Th>
                                    </Table.Tr>
                                </Table.Thead>
                                <Table.Tbody>
                                    {piiMatches.slice(0, 20).map((match, index) => (
                                        <Table.Tr key={index}>
                                            <Table.Td>
                                                <Badge color={piiTypeColors[match.type] || "gray"}>
                                                    {match.type}
                                                </Badge>
                                            </Table.Td>
                                            <Table.Td>
                                                <Text size="sm" ff="monospace">
                                                    {match.text}
                                                </Text>
                                            </Table.Td>
                                            <Table.Td>
                                                <Text size="sm" ff="monospace" c="dimmed">
                                                    [{match.type.toUpperCase()}]
                                                </Text>
                                            </Table.Td>
                                        </Table.Tr>
                                    ))}
                                </Table.Tbody>
                            </Table>
                            {piiMatches.length > 20 && (
                                <Text size="sm" c="dimmed" mt="md">
                                    ... und {piiMatches.length - 20} weitere PII-Matches
                                </Text>
                            )}
                        </ScrollArea>
                    </Paper>
                )}

                {/* Ergebnis */}
                {result && (
                    <Alert
                        icon={result.success ? <IconCheck size={16} /> : <IconAlertTriangle size={16} />}
                        color={result.success ? "green" : "red"}
                        title={result.success ? "Import erfolgreich" : "Import fehlgeschlagen"}
                    >
                        {result.success
                            ? `${result.processed.toLocaleString()} Feedback-Einträge wurden verarbeitet und in den VectorStore geladen.`
                            : "Beim Import ist ein Fehler aufgetreten. Bitte prüfen Sie das Dateiformat."}
                    </Alert>
                )}
            </Stack>
        </Container>
    );
}
