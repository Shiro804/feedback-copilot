"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
    Container,
    Paper,
    Title,
    Text,
    Table,
    Badge,
    Group,
    Select,
    TextInput,
    Pagination,
    Loader,
    Center,
    Anchor,
    Stack,
} from "@mantine/core";
import {
    IconSearch,
    IconMicrophone,
    IconHandFinger,
    IconAlertTriangle,
} from "@tabler/icons-react";
import Link from "next/link";

interface FeedbackItem {
    id: string;
    text: string;
    source_type: string;
    language: string;
    timestamp: string;
    vehicle_model: string;
    market: string;
}

const sourceTypeIcons: Record<string, React.ReactNode> = {
    voice: <IconMicrophone size={14} />,
    touch: <IconHandFinger size={14} />,
    error: <IconAlertTriangle size={14} />,
};

const sourceTypeColors: Record<string, string> = {
    voice: "violet",
    touch: "green",
    error: "red",
};

const sourceTypeLabels: Record<string, string> = {
    voice: "Sprache",
    touch: "Touch",
    error: "Fehler",
};

export default function FeedbacksPage() {
    const searchParams = useSearchParams();
    const [feedbacks, setFeedbacks] = useState<FeedbackItem[]>([]);
    const [filteredFeedbacks, setFilteredFeedbacks] = useState<FeedbackItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState(searchParams.get("search") || "");
    const [filterType, setFilterType] = useState<string | null>(null);
    const [filterModel, setFilterModel] = useState<string | null>(null);
    const [filterMarket, setFilterMarket] = useState<string | null>(null);
    const [page, setPage] = useState(1);
    const itemsPerPage = 15;

    useEffect(() => {
        fetchFeedbacks();
    }, []);

    // Update search from URL params
    useEffect(() => {
        const urlSearch = searchParams.get("search");
        if (urlSearch) {
            setSearch(urlSearch);
        }
    }, [searchParams]);

    useEffect(() => {
        filterData();
    }, [feedbacks, search, filterType, filterModel, filterMarket]);

    const fetchFeedbacks = async () => {
        try {
            const res = await fetch("http://localhost:8000/api/feedbacks/?limit=10000");
            if (res.ok) {
                setFeedbacks(await res.json());
            }
        } catch (e) {
            console.error("Failed to fetch:", e);
        } finally {
            setLoading(false);
        }
    };

    const filterData = () => {
        let filtered = [...feedbacks];

        if (search) {
            const searchLower = search.toLowerCase();
            filtered = filtered.filter(
                (fb) =>
                    fb.text.toLowerCase().includes(searchLower) ||
                    fb.id.toLowerCase().includes(searchLower)
            );
        }

        if (filterType) {
            filtered = filtered.filter((fb) => fb.source_type === filterType);
        }

        if (filterModel) {
            filtered = filtered.filter((fb) => fb.vehicle_model === filterModel);
        }

        if (filterMarket) {
            filtered = filtered.filter((fb) => fb.market === filterMarket);
        }

        setFilteredFeedbacks(filtered);
        setPage(1);
    };

    const paginatedFeedbacks = filteredFeedbacks.slice(
        (page - 1) * itemsPerPage,
        page * itemsPerPage
    );

    const totalPages = Math.ceil(filteredFeedbacks.length / itemsPerPage);

    // Get unique values for filters
    const uniqueModels = [...new Set(feedbacks.map((fb) => fb.vehicle_model).filter(Boolean))];
    const uniqueMarkets = [...new Set(feedbacks.map((fb) => fb.market).filter(Boolean))];

    if (loading) {
        return (
            <Center h="50vh">
                <Loader size="lg" />
            </Center>
        );
    }

    return (
        <Container size="xl">
            <Title order={2} mb="lg">
                Alle Feedbacks
            </Title>

            {/* Filter */}
            <Paper withBorder p="md" radius="md" mb="lg">
                <Group>
                    <TextInput
                        placeholder="Suchen..."
                        leftSection={<IconSearch size={16} />}
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        style={{ flex: 1 }}
                    />
                    <Select
                        placeholder="Typ"
                        data={[
                            { value: "voice", label: "Sprache" },
                            { value: "touch", label: "Touch" },
                            { value: "error", label: "Fehler" },
                        ]}
                        value={filterType}
                        onChange={setFilterType}
                        clearable
                        w={120}
                    />
                    <Select
                        placeholder="Modell"
                        data={uniqueModels.map((m) => ({ value: m, label: m }))}
                        value={filterModel}
                        onChange={setFilterModel}
                        clearable
                        w={120}
                    />
                    <Select
                        placeholder="Markt"
                        data={uniqueMarkets.map((m) => ({ value: m, label: m }))}
                        value={filterMarket}
                        onChange={setFilterMarket}
                        clearable
                        w={100}
                    />
                    <Badge size="lg" variant="light">
                        {filteredFeedbacks.length} Ergebnisse
                    </Badge>
                </Group>
            </Paper>

            {/* Tabelle */}
            <Paper withBorder radius="md">
                <Table striped highlightOnHover>
                    <Table.Thead>
                        <Table.Tr>
                            <Table.Th w={120}>ID</Table.Th>
                            <Table.Th w={100}>Typ</Table.Th>
                            <Table.Th w={100}>Modell</Table.Th>
                            <Table.Th w={60}>Markt</Table.Th>
                            <Table.Th w={50}>Sprache</Table.Th>
                            <Table.Th>Feedback</Table.Th>
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                        {paginatedFeedbacks.map((fb) => (
                            <Table.Tr key={fb.id}>
                                <Table.Td>
                                    <Anchor component={Link} href={`/feedback/${fb.id}`} size="sm" fw={500}>
                                        {fb.id}
                                    </Anchor>
                                </Table.Td>
                                <Table.Td>
                                    <Badge
                                        size="sm"
                                        color={sourceTypeColors[fb.source_type] || "gray"}
                                        leftSection={sourceTypeIcons[fb.source_type]}
                                    >
                                        {sourceTypeLabels[fb.source_type] || fb.source_type}
                                    </Badge>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm">{fb.vehicle_model || "-"}</Text>
                                </Table.Td>
                                <Table.Td>
                                    <Badge size="sm" variant="light">
                                        {fb.market || "-"}
                                    </Badge>
                                </Table.Td>
                                <Table.Td>
                                    <Badge size="xs" variant="outline">
                                        {fb.language.toUpperCase()}
                                    </Badge>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" lineClamp={2}>
                                        {fb.text}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>
                        ))}
                    </Table.Tbody>
                </Table>

                {/* Pagination */}
                {totalPages > 1 && (
                    <Group justify="center" p="md">
                        <Pagination value={page} onChange={setPage} total={totalPages} />
                    </Group>
                )}
            </Paper>
        </Container>
    );
}
