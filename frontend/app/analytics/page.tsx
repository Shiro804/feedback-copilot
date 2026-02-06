"use client";

import { useEffect, useState } from "react";
import {
    Container,
    Paper,
    Title,
    Text,
    Grid,
    Select,
    Group,
    Loader,
    Center,
    Badge,
} from "@mantine/core";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    Legend,
} from "recharts";

// =============================================================================
// TYPES - VW-spezifische Datenstruktur
// =============================================================================

interface FeedbackStats {
    total: number;
    by_label: Record<string, number>;      // Kategorien (NAVIGATION, etc.)
    by_model: Record<string, number>;      // Fahrzeugmodelle (ID.4, Golf 8...)
    by_market: Record<string, number>;     // Märkte (DE, US, UK...)
    by_source: Record<string, number>;     // Quellen (voice, touch, error)
}

interface FeedbackItem {
    id: string;
    text: string;
    label: string;
    vehicle_model: string;
    market: string;
    source_type: string;
}

// =============================================================================
// COLORS
// =============================================================================

const LABEL_COLORS: Record<string, string> = {
    NAVIGATION: "#3b82f6",
    CLIMATE: "#06b6d4",
    INFOTAINMENT: "#f59e0b",
    PHONE_CONNECTIVITY: "#10b981",
    DRIVER_ASSISTANCE: "#8b5cf6",
    SOFTWARE_BUG: "#ef4444",
    PERFORMANCE_RELIABILITY: "#ec4899",
    INTERIOR_ERGONOMICS: "#84cc16",
    DESIGN_AESTHETICS: "#f97316",
    COSTS_ENVIRONMENT: "#14b8a6",
};

const MODEL_COLORS: Record<string, string> = {
    "ID.4": "#3b82f6",
    "ID.3": "#06b6d4",
    "ID.5": "#8b5cf6",
    "ID.7": "#14b8a6",
    "Golf 8": "#22c55e",
    "Tiguan": "#f59e0b",
    "Passat": "#ec4899",
    "Polo": "#84cc16",
    "T-Roc": "#f97316",
    "Touareg": "#ef4444",
};

const MARKET_COLORS: Record<string, string> = {
    DE: "#000000",
    UK: "#1e40af",
    US: "#dc2626",
    FR: "#2563eb",
    CN: "#dc2626",
    NL: "#f97316",
    AT: "#ef4444",
    CH: "#dc2626",
    BE: "#fbbf24",
    NO: "#0ea5e9",
};

const SOURCE_COLORS: Record<string, string> = {
    voice: "#8b5cf6",
    touch: "#3b82f6",
    error: "#ef4444",
    survey: "#22c55e",
};

// =============================================================================
// COMPONENT
// =============================================================================

export default function AnalyticsPage() {
    const [stats, setStats] = useState<FeedbackStats | null>(null);
    const [feedbacks, setFeedbacks] = useState<FeedbackItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [filterLabel, setFilterLabel] = useState<string | null>(null);
    const [filterModel, setFilterModel] = useState<string | null>(null);

    useEffect(() => {
        fetchData();
    }, [filterLabel, filterModel]);

    const fetchData = async () => {
        try {
            let url = "http://localhost:8000/api/feedbacks/?limit=10000";
            if (filterLabel) url += `&label=${filterLabel}`;
            if (filterModel) url += `&vehicle_model=${filterModel}`;

            const [statsRes, feedbacksRes] = await Promise.all([
                fetch("http://localhost:8000/api/feedbacks/stats"),
                fetch(url),
            ]);

            if (statsRes.ok) setStats(await statsRes.json());
            if (feedbacksRes.ok) setFeedbacks(await feedbacksRes.json());
        } catch (error) {
            console.error("Failed to fetch data:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Center h="50vh">
                <Loader size="lg" />
            </Center>
        );
    }

    // =============================================================================
    // CHART DATA PREPARATION
    // =============================================================================

    // Nach Kategorie (Label)
    const labelData = stats?.by_label
        ? Object.entries(stats.by_label)
            .map(([name, count]) => ({
                name,
                count,
                color: LABEL_COLORS[name] || "#6b7280",
            }))
            .sort((a, b) => b.count - a.count)
        : [];

    // Nach Fahrzeugmodell
    const modelData = stats?.by_model
        ? Object.entries(stats.by_model)
            .map(([name, count]) => ({
                name,
                count,
                color: MODEL_COLORS[name] || "#6b7280",
            }))
            .sort((a, b) => b.count - a.count)
        : [];

    // Nach Markt
    const marketData = stats?.by_market
        ? Object.entries(stats.by_market)
            .map(([name, count]) => ({
                name,
                count,
                color: MARKET_COLORS[name] || "#6b7280",
            }))
            .sort((a, b) => b.count - a.count)
        : [];

    // Nach Quelle (source_type)
    const sourceData = stats?.by_source
        ? Object.entries(stats.by_source)
            .map(([name, count]) => ({
                name: name === "voice" ? "🎤 Voice" : name === "touch" ? "👆 Touch" : name === "error" ? "⚠️ Error" : "📋 Survey",
                rawName: name,
                count,
                color: SOURCE_COLORS[name] || "#6b7280",
            }))
        : [];

    // Filter-Optionen
    const labelOptions = stats?.by_label
        ? [
            { value: "", label: "Alle Kategorien" },
            ...Object.keys(stats.by_label).map(label => ({
                value: label,
                label: label.replace("_", " "),
            })),
        ]
        : [{ value: "", label: "Alle Kategorien" }];

    const modelOptions = stats?.by_model
        ? [
            { value: "", label: "Alle Modelle" },
            ...Object.keys(stats.by_model).map(model => ({
                value: model,
                label: model,
            })),
        ]
        : [{ value: "", label: "Alle Modelle" }];

    return (
        <Container size="xl">
            <Group justify="space-between" mb="lg">
                <Title order={2}>📊 Feedback Analytics</Title>
                <Group>
                    <Badge size="lg" variant="gradient" gradient={{ from: "blue", to: "cyan" }}>
                        {stats?.total?.toLocaleString() ?? 0} Feedbacks
                    </Badge>
                    <Select
                        placeholder="Kategorie"
                        data={labelOptions}
                        value={filterLabel}
                        onChange={setFilterLabel}
                        clearable
                        w={180}
                    />
                    <Select
                        placeholder="Fahrzeugmodell"
                        data={modelOptions}
                        value={filterModel}
                        onChange={setFilterModel}
                        clearable
                        w={180}
                    />
                </Group>
            </Group>

            <Grid>
                {/* Nach Kategorie (Label) - Horizontal Bar Chart */}
                <Grid.Col span={12}>
                    <Paper withBorder p="lg" radius="md">
                        <Text fw={500} mb="md">
                            📁 Nach Kategorie
                        </Text>
                        <ResponsiveContainer width="100%" height={350}>
                            <BarChart data={labelData} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis type="number" />
                                <YAxis dataKey="name" type="category" width={180} tick={{ fontSize: 11 }} />
                                <Tooltip formatter={(value: number | undefined) => value?.toLocaleString() ?? ''} />
                                <Bar dataKey="count" radius={4}>
                                    {labelData.map((entry, index) => (
                                        <Cell key={index} fill={entry.color} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </Paper>
                </Grid.Col>

                {/* Nach Fahrzeugmodell - Bar Chart */}
                <Grid.Col span={{ base: 12, md: 6 }}>
                    <Paper withBorder p="lg" radius="md" h="100%">
                        <Text fw={500} mb="md">
                            🚗 Nach Fahrzeugmodell
                        </Text>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={modelData.slice(0, 10)} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis type="number" />
                                <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 11 }} />
                                <Tooltip formatter={(value: number | undefined) => value?.toLocaleString() ?? ''} />
                                <Bar dataKey="count" radius={4}>
                                    {modelData.slice(0, 10).map((entry, index) => (
                                        <Cell key={index} fill={entry.color} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </Paper>
                </Grid.Col>

                {/* Nach Markt - Pie Chart */}
                <Grid.Col span={{ base: 12, md: 6 }}>
                    <Paper withBorder p="lg" radius="md" h="100%">
                        <Text fw={500} mb="md">
                            🌍 Nach Markt
                        </Text>
                        <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                                <Pie
                                    data={marketData.slice(0, 8)}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={50}
                                    outerRadius={100}
                                    paddingAngle={2}
                                    dataKey="count"
                                    label={({ name }) => name}
                                >
                                    {marketData.slice(0, 8).map((entry, index) => (
                                        <Cell key={index} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip formatter={(value: number | undefined) => value?.toLocaleString() ?? ''} />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </Paper>
                </Grid.Col>

                {/* Nach Quelle - Pie Chart */}
                <Grid.Col span={{ base: 12, md: 4 }}>
                    <Paper withBorder p="lg" radius="md" h="100%">
                        <Text fw={500} mb="md">
                            📱 Nach Quelle
                        </Text>
                        <ResponsiveContainer width="100%" height={280}>
                            <PieChart>
                                <Pie
                                    data={sourceData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={50}
                                    outerRadius={90}
                                    paddingAngle={2}
                                    dataKey="count"
                                    label={({ name, percent }) => `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`}
                                    labelLine={false}
                                >
                                    {sourceData.map((entry, index) => (
                                        <Cell key={index} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip formatter={(value: number | undefined) => value?.toLocaleString() ?? ''} />
                            </PieChart>
                        </ResponsiveContainer>
                    </Paper>
                </Grid.Col>

                {/* Zusammenfassung */}
                <Grid.Col span={{ base: 12, md: 8 }}>
                    <Paper withBorder p="lg" radius="md">
                        <Text fw={500} mb="md">
                            📋 VW Feedback-Übersicht
                        </Text>
                        <Grid>
                            <Grid.Col span={4}>
                                <Text size="sm" c="dimmed">Gesamt Feedbacks</Text>
                                <Text size="xl" fw={700} c="blue">{stats?.total?.toLocaleString() ?? 0}</Text>
                            </Grid.Col>
                            <Grid.Col span={4}>
                                <Text size="sm" c="dimmed">Kategorien</Text>
                                <Text size="xl" fw={700}>{Object.keys(stats?.by_label ?? {}).length}</Text>
                            </Grid.Col>
                            <Grid.Col span={4}>
                                <Text size="sm" c="dimmed">Fahrzeugmodelle</Text>
                                <Text size="xl" fw={700} c="violet">{Object.keys(stats?.by_model ?? {}).length}</Text>
                            </Grid.Col>
                            <Grid.Col span={4}>
                                <Text size="sm" c="dimmed">Märkte</Text>
                                <Text size="xl" fw={700} c="teal">{Object.keys(stats?.by_market ?? {}).length}</Text>
                            </Grid.Col>
                            <Grid.Col span={4}>
                                <Text size="sm" c="dimmed">🎤 Voice Feedbacks</Text>
                                <Text size="xl" fw={700} c="grape">{(stats?.by_source?.voice ?? 0).toLocaleString()}</Text>
                            </Grid.Col>
                            <Grid.Col span={4}>
                                <Text size="sm" c="dimmed">🇩🇪 Deutsche Feedbacks</Text>
                                <Text size="xl" fw={700}>{(stats?.by_market?.DE ?? 0).toLocaleString()}</Text>
                            </Grid.Col>
                        </Grid>
                    </Paper>
                </Grid.Col>
            </Grid>
        </Container>
    );
}
