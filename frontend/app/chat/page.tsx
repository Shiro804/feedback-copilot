"use client";

import { useState, useRef, useEffect } from "react";
import {
    Container,
    Paper,
    TextInput,
    Button,
    Stack,
    Text,
    Group,
    Badge,
    ScrollArea,
    Loader,
    ThemeIcon,
    Alert,
    Tooltip,
    Grid,
    ActionIcon,
} from "@mantine/core";
import {
    IconSend,
    IconRobot,
    IconUser,
    IconLink,
    IconAlertCircle,
    IconHistory,
    IconTrash,
} from "@tabler/icons-react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";

interface Source {
    id: string;
    text: string;
    score: number;
    metadata?: Record<string, string>;
}

interface Message {
    role: "user" | "assistant";
    content: string;
    sources?: Source[];
    answerable?: boolean;
}

interface HistoryItem {
    question: string;
    answer: string;
    timestamp: string;
    sources_count: number;
    sources: Source[];
}

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [selectedHistoryIndex, setSelectedHistoryIndex] = useState<number | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    useEffect(() => {
        fetchHistory();
    }, []);

    const fetchHistory = async () => {
        try {
            const res = await fetch("http://localhost:8000/api/chat/history");
            if (res.ok) {
                const data = await res.json();
                setHistory(data);

                // Automatisch neuesten Eintrag laden
                if (data.length > 0 && messages.length === 0) {
                    loadHistoryItem(data[0], 0);
                }
            }
        } catch (e) {
            console.error("Failed to fetch history:", e);
        }
    };

    const clearHistory = async () => {
        try {
            await fetch("http://localhost:8000/api/chat/history", { method: "DELETE" });
            setHistory([]);
            setMessages([]);
            setSelectedHistoryIndex(null);
        } catch (e) {
            console.error("Failed to clear history:", e);
        }
    };

    const loadHistoryItem = (item: HistoryItem, index: number) => {
        // Lade die komplette Konversation
        setMessages([
            { role: "user", content: item.question },
            {
                role: "assistant",
                content: item.answer,
                sources: item.sources,
                answerable: true
            }
        ]);
        setSelectedHistoryIndex(index);
    };

    const handleSubmit = async () => {
        if (!input.trim() || loading) return;

        const question = input;
        const userMessage: Message = { role: "user", content: question };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setLoading(true);

        try {
            const response = await fetch("http://localhost:8000/api/chat/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question, language: "de" }),
            });

            const data = await response.json();

            const assistantMessage: Message = {
                role: "assistant",
                content: data.answer,
                sources: data.sources,
                answerable: data.answerable,
            };

            setMessages((prev) => [...prev, assistantMessage]);

            // History aktualisieren und neuesten auswählen
            await fetchHistory();
            setSelectedHistoryIndex(0);
        } catch (error) {
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: "Fehler bei der Verbindung zum Backend.",
                    answerable: false,
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const startNewChat = () => {
        setMessages([]);
        setSelectedHistoryIndex(null);
        setInput("");
    };

    return (
        <Container size="xl" h="calc(100vh - 120px)">
            <Grid h="100%">
                {/* History Sidebar */}
                <Grid.Col span={3}>
                    <Paper withBorder p="md" radius="md" h="100%">
                        <Group justify="space-between" mb="md">
                            <Group gap="xs">
                                <IconHistory size={18} />
                                <Text fw={500} size="sm">
                                    Verlauf
                                </Text>
                            </Group>
                            <Group gap="xs">
                                <Button size="xs" variant="light" onClick={startNewChat}>
                                    Neu
                                </Button>
                                {history.length > 0 && (
                                    <ActionIcon
                                        variant="subtle"
                                        color="red"
                                        size="sm"
                                        onClick={clearHistory}
                                    >
                                        <IconTrash size={14} />
                                    </ActionIcon>
                                )}
                            </Group>
                        </Group>
                        <ScrollArea h="calc(100% - 50px)">
                            <Stack gap="xs">
                                {history.length === 0 && (
                                    <Text size="xs" c="dimmed" ta="center">
                                        Noch keine Anfragen
                                    </Text>
                                )}
                                {history.map((item, index) => (
                                    <Paper
                                        key={index}
                                        p="xs"
                                        radius="sm"
                                        bg={selectedHistoryIndex === index ? "blue.0" : "gray.0"}
                                        style={{
                                            cursor: "pointer",
                                            border: selectedHistoryIndex === index ? "1px solid var(--mantine-color-blue-4)" : "none"
                                        }}
                                        onClick={() => loadHistoryItem(item, index)}
                                    >
                                        <Text size="xs" lineClamp={2} fw={500}>
                                            {item.question}
                                        </Text>
                                        <Group gap="xs" mt={4}>
                                            <Badge size="xs" variant="light">
                                                {item.sources_count} Quellen
                                            </Badge>
                                            <Text size="xs" c="dimmed">
                                                {new Date(item.timestamp).toLocaleTimeString("de-DE", {
                                                    hour: "2-digit",
                                                    minute: "2-digit",
                                                })}
                                            </Text>
                                        </Group>
                                    </Paper>
                                ))}
                            </Stack>
                        </ScrollArea>
                    </Paper>
                </Grid.Col>

                {/* Chat Area */}
                <Grid.Col span={9}>
                    <Stack h="100%" gap="md">
                        {/* Chat Header */}
                        <Paper withBorder p="md" radius="md">
                            <Group>
                                <ThemeIcon size="lg" variant="light" color="blue">
                                    <IconRobot size={24} />
                                </ThemeIcon>
                                <div>
                                    <Text fw={600}>Feedback-Copilot Chat</Text>
                                    <Text size="sm" c="dimmed">
                                        RAG-basierte Analyse mit Quellenangabe
                                    </Text>
                                </div>
                            </Group>
                        </Paper>

                        {/* Messages */}
                        <Paper withBorder p="md" radius="md" style={{ flex: 1, overflow: "hidden" }}>
                            <ScrollArea h="100%" pr="md">
                                <Stack gap="md">
                                    {messages.length === 0 && (
                                        <Text c="dimmed" ta="center" py="xl">
                                            Stelle eine Frage zu den Kundenfeedbacks...
                                        </Text>
                                    )}

                                    {messages.map((message, index) => (
                                        <Paper
                                            key={index}
                                            p="md"
                                            radius="md"
                                            bg={message.role === "user" ? "blue.0" : "gray.0"}
                                        >
                                            <Group align="flex-start" gap="sm">
                                                <ThemeIcon
                                                    variant="light"
                                                    color={message.role === "user" ? "blue" : "gray"}
                                                    size="sm"
                                                >
                                                    {message.role === "user" ? (
                                                        <IconUser size={14} />
                                                    ) : (
                                                        <IconRobot size={14} />
                                                    )}
                                                </ThemeIcon>
                                                <div style={{ flex: 1 }}>
                                                    <div style={{ fontSize: '0.875rem' }}>
                                                        <ReactMarkdown
                                                            components={{
                                                                p: ({ children }) => <Text size="sm" mb="xs">{children}</Text>,
                                                                strong: ({ children }) => <Text span fw={600}>{children}</Text>,
                                                                ul: ({ children }) => <ul style={{ marginLeft: '1rem', marginTop: '0.5rem', marginBottom: '0.5rem' }}>{children}</ul>,
                                                                ol: ({ children }) => <ol style={{ marginLeft: '1rem', marginTop: '0.5rem', marginBottom: '0.5rem' }}>{children}</ol>,
                                                                li: ({ children }) => <li style={{ marginBottom: '0.25rem' }}><Text size="sm" span>{children}</Text></li>,
                                                            }}
                                                        >
                                                            {message.content}
                                                        </ReactMarkdown>
                                                    </div>

                                                    {/* Quellen anzeigen - klickbar zur Einzelansicht */}
                                                    {message.sources && message.sources.length > 0 && (
                                                        <Group gap="xs" mt="sm">
                                                            <IconLink size={14} color="gray" />
                                                            {message.sources.map((source) => (
                                                                <Tooltip
                                                                    key={source.id}
                                                                    label={
                                                                        <div>
                                                                            <Text size="xs" fw={500}>{source.id}</Text>
                                                                            <Text size="xs">{source.text || "Keine Details"}</Text>
                                                                            <Text size="xs" c="dimmed" mt={4}>
                                                                                Klicken für Einzelansicht
                                                                            </Text>
                                                                        </div>
                                                                    }
                                                                    multiline
                                                                    w={350}
                                                                    withArrow
                                                                    position="top"
                                                                >
                                                                    <Badge
                                                                        component={Link}
                                                                        href={`/feedback/${source.id}`}
                                                                        size="sm"
                                                                        variant="light"
                                                                        color="blue"
                                                                        style={{ cursor: "pointer", textDecoration: "none" }}
                                                                    >
                                                                        {source.id} ({(source.score * 100).toFixed(0)}%)
                                                                    </Badge>
                                                                </Tooltip>
                                                            ))}
                                                        </Group>
                                                    )}

                                                    {/* Unanswerable Warning */}
                                                    {message.answerable === false && (
                                                        <Alert
                                                            icon={<IconAlertCircle size={16} />}
                                                            color="yellow"
                                                            mt="sm"
                                                            p="xs"
                                                        >
                                                            Keine ausreichende Evidenz in den Daten
                                                        </Alert>
                                                    )}
                                                </div>
                                            </Group>
                                        </Paper>
                                    ))}

                                    {loading && (
                                        <Group>
                                            <Loader size="sm" />
                                            <Text size="sm" c="dimmed">
                                                Analysiere Feedbacks...
                                            </Text>
                                        </Group>
                                    )}

                                    <div ref={scrollRef} />
                                </Stack>
                            </ScrollArea>
                        </Paper>

                        {/* Input */}
                        <Paper withBorder p="md" radius="md">
                            <Group>
                                <TextInput
                                    placeholder="Welche Probleme gibt es mit dem Sprachassistenten?"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
                                    style={{ flex: 1 }}
                                    disabled={loading}
                                />
                                <Button
                                    onClick={handleSubmit}
                                    loading={loading}
                                    leftSection={<IconSend size={16} />}
                                >
                                    Senden
                                </Button>
                            </Group>
                        </Paper>
                    </Stack>
                </Grid.Col>
            </Grid>
        </Container>
    );
}
