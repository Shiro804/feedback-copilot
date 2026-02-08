"use client";

import { useState, useEffect } from "react";
import {
    Container,
    Paper,
    Title,
    Text,
    Grid,
    Textarea,
    Button,
    Group,
    Select,
    Stack,
    Badge,
    Alert,
    Loader,
    Center,
    MultiSelect,
} from "@mantine/core";
import {
    IconFileExport,
    IconTicket,
    IconFileDescription,
    IconCheck,
    IconDownload,
} from "@tabler/icons-react";

// =============================================================================
// TYPES - VW-spezifische Datenstruktur
// =============================================================================

interface FeedbackItem {
    id: string;
    text: string;
    label: string;           // Kategorie (NAVIGATION, etc.)
    vehicle_model: string;   // ID.4, Golf 8, etc.
    market: string;          // DE, US, UK, etc.
    source_type: string;     // voice, touch, error, survey
    language: string;
    timestamp: string;
    confidence: number;
}

export default function ExportPage() {
    const [feedbacks, setFeedbacks] = useState<FeedbackItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [ticketContent, setTicketContent] = useState("");
    const [pdfUrl, setPdfUrl] = useState<string | null>(null);
    const [pdfLoading, setPdfLoading] = useState(false);
    const [format, setFormat] = useState<string | null>("json");
    const [exportType, setExportType] = useState<string | null>("ticket");
    const [selectedLabels, setSelectedLabels] = useState<string[]>([]);
    const [selectedModels, setSelectedModels] = useState<string[]>([]);
    const [selectedMarkets, setSelectedMarkets] = useState<string[]>([]);
    const [exported, setExported] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const res = await fetch("http://localhost:8000/api/feedbacks/?limit=50000");
            if (res.ok) setFeedbacks(await res.json());
        } catch (e) {
            console.error("Failed to fetch:", e);
        } finally {
            setLoading(false);
        }
    };

    // Dynamische Filter-Optionen
    const uniqueLabels = [...new Set(feedbacks.map((fb) => fb.label).filter(Boolean))];
    const uniqueModels = [...new Set(feedbacks.map((fb) => fb.vehicle_model).filter(Boolean))];
    const uniqueMarkets = [...new Set(feedbacks.map((fb) => fb.market).filter(Boolean))];

    const generateExport = async () => {
        // Filter feedbacks locally first
        let filtered = feedbacks;
        if (selectedLabels.length > 0) {
            filtered = filtered.filter((fb) => selectedLabels.includes(fb.label));
        }
        if (selectedModels.length > 0) {
            filtered = filtered.filter((fb) => selectedModels.includes(fb.vehicle_model));
        }
        if (selectedMarkets.length > 0) {
            filtered = filtered.filter((fb) => selectedMarkets.includes(fb.market));
        }

        // PDF Preview generieren
        if (format === "pdf") {
            setPdfLoading(true);
            setTicketContent("");
            try {
                // Alle Filter als komma-separierte Werte senden
                const params = new URLSearchParams();
                if (selectedLabels.length > 0) {
                    selectedLabels.forEach(l => params.append("label", l));
                }
                if (selectedModels.length > 0) {
                    selectedModels.forEach(m => params.append("vehicle_model", m));
                }
                if (selectedMarkets.length > 0) {
                    selectedMarkets.forEach(m => params.append("market", m));
                }
                // Kein Limit mehr - alle gefilterten ausgeben
                params.append("limit", String(Math.min(filtered.length, 500)));

                const response = await fetch(`http://localhost:8000/api/export/pdf?${params}`);
                if (!response.ok) throw new Error("PDF Generierung fehlgeschlagen");

                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                setPdfUrl(url);
            } catch (e) {
                console.error("PDF Preview failed:", e);
            } finally {
                setPdfLoading(false);
            }
            return;
        }

        setPdfUrl(null);

        if (exportType === "ticket") {
            // Gruppierung nach Label
            const byLabel = Object.entries(
                filtered.reduce((acc, fb) => {
                    const key = fb.label || "UNKNOWN";
                    acc[key] = (acc[key] || 0) + 1;
                    return acc;
                }, {} as Record<string, number>)
            ).sort((a, b) => b[1] - a[1]);

            // Gruppierung nach Modell
            const byModel = Object.entries(
                filtered.reduce((acc, fb) => {
                    const key = fb.vehicle_model || "unknown";
                    acc[key] = (acc[key] || 0) + 1;
                    return acc;
                }, {} as Record<string, number>)
            ).sort((a, b) => b[1] - a[1]);

            // Gruppierung nach Markt
            const byMarket = Object.entries(
                filtered.reduce((acc, fb) => {
                    const key = fb.market || "unknown";
                    acc[key] = (acc[key] || 0) + 1;
                    return acc;
                }, {} as Record<string, number>)
            ).sort((a, b) => b[1] - a[1]);

            const ticket = {
                title: "Feedback-Bericht",
                generated: new Date().toISOString(),
                total_feedbacks: filtered.length,
                filters: {
                    labels: selectedLabels.length > 0 ? selectedLabels : "Alle",
                    models: selectedModels.length > 0 ? selectedModels : "Alle",
                    markets: selectedMarkets.length > 0 ? selectedMarkets : "Alle",
                },
                summary: {
                    by_label: byLabel.map(([label, count]) => ({ label, count })),
                    by_model: byModel.map(([model, count]) => ({ model, count })),
                    by_market: byMarket.map(([market, count]) => ({ market, count })),
                },
                feedbacks: filtered.slice(0, 1000).map((fb) => ({
                    id: fb.id,
                    text: fb.text,
                    label: fb.label,
                    vehicle_model: fb.vehicle_model,
                    market: fb.market,
                    source_type: fb.source_type,
                })),
            };

            if (format === "json") {
                setTicketContent(JSON.stringify(ticket, null, 2));
            } else if (format === "csv") {
                const header = "id,text,label,vehicle_model,market,source_type";
                const rows = filtered.slice(0, 1000).map(
                    (fb) =>
                        `"${fb.id}","${fb.text.replace(/"/g, '""')}","${fb.label}","${fb.vehicle_model}","${fb.market}","${fb.source_type}"`
                );
                setTicketContent([header, ...rows].join("\n"));
            } else if (format === "md") {
                const md = `# Feedback-Bericht

**Generiert:** ${new Date().toLocaleString("de-DE")}  
**Anzahl:** ${filtered.length.toLocaleString()} Feedbacks

## Filter
- **Kategorien:** ${selectedLabels.length > 0 ? selectedLabels.join(", ") : "Alle"}
- **Modelle:** ${selectedModels.length > 0 ? selectedModels.join(", ") : "Alle"}
- **Märkte:** ${selectedMarkets.length > 0 ? selectedMarkets.join(", ") : "Alle"}

## Übersicht nach Kategorie
${byLabel.map(([label, count]) => `- **${label}:** ${count.toLocaleString()}`).join("\n")}

## Übersicht nach Modell
${byModel.map(([model, count]) => `- **${model}:** ${count.toLocaleString()}`).join("\n")}

## Übersicht nach Markt
${byMarket.map(([market, count]) => `- **${market}:** ${count.toLocaleString()}`).join("\n")}

## Feedbacks (Top 20)

${filtered.slice(0, 20).map((fb) => `### ${fb.id}
- **Kategorie:** ${fb.label}
- **Modell:** ${fb.vehicle_model}
- **Markt:** ${fb.market}
- **Quelle:** ${fb.source_type}

> ${fb.text}
`).join("\n")}
${filtered.length > 20 ? `\n*... und ${(filtered.length - 20).toLocaleString()} weitere Feedbacks*` : ""}
`;
                setTicketContent(md);
            }
        } else if (exportType === "stats") {
            // Nur Statistiken
            const byLabel = Object.entries(
                filtered.reduce((acc, fb) => {
                    acc[fb.label] = (acc[fb.label] || 0) + 1;
                    return acc;
                }, {} as Record<string, number>)
            ).sort((a, b) => b[1] - a[1]);

            const byModel = Object.entries(
                filtered.reduce((acc, fb) => {
                    acc[fb.vehicle_model] = (acc[fb.vehicle_model] || 0) + 1;
                    return acc;
                }, {} as Record<string, number>)
            ).sort((a, b) => b[1] - a[1]);

            if (format === "json") {
                setTicketContent(JSON.stringify({ total: filtered.length, by_label: Object.fromEntries(byLabel), by_model: Object.fromEntries(byModel) }, null, 2));
            } else {
                setTicketContent(`# Statistiken

**Gesamt:** ${filtered.length.toLocaleString()} Feedbacks

## Nach Kategorie
${byLabel.map(([k, v]) => `- **${k}:** ${v.toLocaleString()}`).join("\n")}

## Nach Modell
${byModel.map(([k, v]) => `- **${k}:** ${v.toLocaleString()}`).join("\n")}`);
            }
        }
    };

    const handleExport = async () => {
        // PDF herunterladen
        if (format === "pdf" && pdfUrl) {
            const a = document.createElement("a");
            a.href = pdfUrl;
            a.download = `feedback-export.pdf`;
            a.click();
            setExported(true);
            setTimeout(() => setExported(false), 3000);
            return;
        }

        const blob = new Blob([ticketContent], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `feedback-export.${format}`;
        a.click();
        setExported(true);
        setTimeout(() => setExported(false), 3000);
    };

    if (loading) {
        return (
            <Center h="50vh">
                <Loader size="lg" />
            </Center>
        );
    }

    // Gefilterte Anzahl
    const filteredCount = feedbacks.filter((fb) => {
        if (selectedLabels.length > 0 && !selectedLabels.includes(fb.label)) return false;
        if (selectedModels.length > 0 && !selectedModels.includes(fb.vehicle_model)) return false;
        if (selectedMarkets.length > 0 && !selectedMarkets.includes(fb.market)) return false;
        return true;
    }).length;

    return (
        <Container size="lg">
            <Title order={2} mb="lg">
                📤 Export
            </Title>

            <Grid>
                {/* Export-Optionen */}
                <Grid.Col span={{ base: 12, md: 5 }}>
                    <Paper withBorder p="lg" radius="md" h="100%">
                        <Group mb="md">
                            <IconTicket size={24} color="var(--mantine-color-blue-6)" />
                            <Text fw={500}>Export konfigurieren</Text>
                        </Group>

                        <Stack gap="md">
                            <Select
                                label="Export-Typ"
                                data={[
                                    { value: "ticket", label: "Vollständiger Bericht" },
                                    { value: "stats", label: "Nur Statistiken" },
                                ]}
                                value={exportType}
                                onChange={setExportType}
                            />

                            <Select
                                label="Format"
                                data={[
                                    { value: "json", label: "JSON" },
                                    { value: "csv", label: "CSV" },
                                    { value: "md", label: "Markdown" },
                                    { value: "pdf", label: "PDF" },
                                ]}
                                value={format}
                                onChange={setFormat}
                            />

                            <MultiSelect
                                label="Kategorien"
                                placeholder="Alle Kategorien"
                                data={uniqueLabels.map(l => ({ value: l, label: l.replace("_", " ") }))}
                                value={selectedLabels}
                                onChange={setSelectedLabels}
                                clearable
                                searchable
                            />

                            <MultiSelect
                                label="Fahrzeugmodelle"
                                placeholder="Alle Modelle"
                                data={uniqueModels.map(m => ({ value: m, label: m }))}
                                value={selectedModels}
                                onChange={setSelectedModels}
                                clearable
                                searchable
                            />

                            <MultiSelect
                                label="Märkte"
                                placeholder="Alle Märkte"
                                data={uniqueMarkets.map(m => ({ value: m, label: m }))}
                                value={selectedMarkets}
                                onChange={setSelectedMarkets}
                                clearable
                            />

                            <Badge size="lg" variant="gradient" gradient={{ from: "blue", to: "cyan" }}>
                                {filteredCount.toLocaleString()} Feedbacks ausgewählt
                            </Badge>

                            <Button
                                onClick={generateExport}
                                leftSection={<IconFileExport size={16} />}
                                fullWidth
                            >
                                Generieren
                            </Button>
                        </Stack>
                    </Paper>
                </Grid.Col>

                {/* Preview */}
                <Grid.Col span={{ base: 12, md: 7 }}>
                    <Paper withBorder p="lg" radius="md" h="100%">
                        <Group mb="md" justify="space-between">
                            <Group>
                                <IconFileDescription size={24} color="var(--mantine-color-gray-6)" />
                                <Text fw={500}>Vorschau</Text>
                            </Group>
                            {format && <Badge>{format.toUpperCase()}</Badge>}
                        </Group>

                        {/* PDF Preview */}
                        {format === "pdf" && pdfLoading && (
                            <Center h={400}>
                                <Stack align="center">
                                    <Loader size="lg" />
                                    <Text c="dimmed">PDF wird generiert...</Text>
                                </Stack>
                            </Center>
                        )}

                        {format === "pdf" && pdfUrl && !pdfLoading && (
                            <object
                                data={pdfUrl}
                                type="application/pdf"
                                style={{
                                    width: "100%",
                                    height: "600px",
                                    border: "1px solid #ddd",
                                    borderRadius: "8px",
                                    overflow: "auto"
                                }}
                            >
                                <iframe
                                    src={pdfUrl}
                                    style={{ width: "100%", height: "600px", border: "none" }}
                                    title="PDF Preview"
                                />
                            </object>
                        )}

                        {format === "pdf" && !pdfUrl && !pdfLoading && (
                            <Center h={400}>
                                <Text c="dimmed">Klicke 'Generieren' um PDF-Vorschau zu laden...</Text>
                            </Center>
                        )}

                        {/* Text Preview */}
                        {format !== "pdf" && (
                            <Textarea
                                value={ticketContent}
                                readOnly
                                placeholder="Klicke 'Generieren' um einen Export zu erstellen..."
                                minRows={25}
                                autosize
                                maxRows={40}
                                styles={{ input: { fontFamily: "monospace", fontSize: 12, backgroundColor: "#f9f9f9" } }}
                            />
                        )}

                        <Button
                            mt="md"
                            onClick={handleExport}
                            disabled={(format !== "pdf" && !ticketContent) || (format === "pdf" && !pdfUrl)}
                            leftSection={<IconDownload size={16} />}
                            fullWidth
                        >
                            Herunterladen
                        </Button>

                        {exported && (
                            <Alert
                                icon={<IconCheck size={16} />}
                                color="green"
                                mt="md"
                                title="Exportiert"
                            >
                                Datei wurde heruntergeladen.
                            </Alert>
                        )}
                    </Paper>
                </Grid.Col>
            </Grid>
        </Container>
    );
}
