"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
    Container,
    Paper,
    Title,
    Text,
    Group,
    Badge,
    Button,
    Loader,
    Center,
    Stack,
    Divider,
} from "@mantine/core";
import {
    IconArrowLeft,
    IconMicrophone,
    IconHandFinger,
    IconAlertTriangle,
    IconCar,
    IconWorld,
    IconLanguage,
    IconClock,
} from "@tabler/icons-react";

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
    voice: <IconMicrophone size={20} />,
    touch: <IconHandFinger size={20} />,
    error: <IconAlertTriangle size={20} />,
};

const sourceTypeColors: Record<string, string> = {
    voice: "violet",
    touch: "green",
    error: "red",
};

export default function FeedbackDetailPage() {
    const params = useParams();
    const router = useRouter();
    const [feedback, setFeedback] = useState<FeedbackItem | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchFeedback() {
            try {
                const res = await fetch(
                    `http://localhost:8000/api/feedbacks/${params.id}`
                );
                if (res.ok) {
                    setFeedback(await res.json());
                } else {
                    setError("Feedback nicht gefunden");
                }
            } catch (e) {
                setError("Fehler beim Laden");
            } finally {
                setLoading(false);
            }
        }

        if (params.id) {
            fetchFeedback();
        }
    }, [params.id]);

    if (loading) {
        return (
            <Center h="50vh">
                <Loader size="lg" />
            </Center>
        );
    }

    if (error || !feedback) {
        return (
            <Container size="md">
                <Paper withBorder p="xl" radius="md">
                    <Text c="red" ta="center">
                        {error || "Feedback nicht gefunden"}
                    </Text>
                    <Center mt="md">
                        <Button variant="light" onClick={() => router.back()}>
                            Zurück
                        </Button>
                    </Center>
                </Paper>
            </Container>
        );
    }

    return (
        <Container size="md">
            <Button
                variant="subtle"
                leftSection={<IconArrowLeft size={16} />}
                onClick={() => router.back()}
                mb="md"
            >
                Zurück
            </Button>

            <Paper withBorder p="xl" radius="md">
                <Group justify="space-between" mb="lg">
                    <Title order={3}>{feedback.id}</Title>
                    <Badge
                        size="lg"
                        color={sourceTypeColors[feedback.source_type] || "gray"}
                        leftSection={sourceTypeIcons[feedback.source_type]}
                    >
                        {feedback.source_type}
                    </Badge>
                </Group>

                <Divider mb="lg" />

                {/* Feedback Text */}
                <Paper bg="gray.0" p="md" radius="md" mb="lg">
                    <Text size="lg">{feedback.text}</Text>
                </Paper>

                {/* Metadaten */}
                <Title order={5} mb="md">
                    Metadaten
                </Title>
                <Stack gap="sm">
                    <Group>
                        <IconCar size={18} color="gray" />
                        <Text size="sm" c="dimmed" w={120}>
                            Fahrzeugmodell:
                        </Text>
                        <Text size="sm" fw={500}>
                            {feedback.vehicle_model || "Nicht angegeben"}
                        </Text>
                    </Group>

                    <Group>
                        <IconWorld size={18} color="gray" />
                        <Text size="sm" c="dimmed" w={120}>
                            Markt:
                        </Text>
                        <Text size="sm" fw={500}>
                            {feedback.market || "Nicht angegeben"}
                        </Text>
                    </Group>

                    <Group>
                        <IconLanguage size={18} color="gray" />
                        <Text size="sm" c="dimmed" w={120}>
                            Sprache:
                        </Text>
                        <Badge size="sm" variant="light">
                            {feedback.language.toUpperCase()}
                        </Badge>
                    </Group>

                    <Group>
                        <IconClock size={18} color="gray" />
                        <Text size="sm" c="dimmed" w={120}>
                            Zeitstempel:
                        </Text>
                        <Text size="sm" fw={500}>
                            {feedback.timestamp
                                ? new Date(feedback.timestamp).toLocaleString("de-DE")
                                : "Nicht angegeben"}
                        </Text>
                    </Group>
                </Stack>
            </Paper>
        </Container>
    );
}
