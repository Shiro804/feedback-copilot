"use client";

import { useEffect, useState } from "react";
import {
  Container,
  Grid,
  Paper,
  Text,
  Group,
  RingProgress,
  SimpleGrid,
  Title,
  Table,
  Badge,
  Loader,
  Center,
  Anchor,
  Stack,
} from "@mantine/core";
import {
  IconMessage,
  IconMicrophone,
  IconHandFinger,
  IconAlertTriangle,
  IconCar,
  IconWorld,
} from "@tabler/icons-react";
import Link from "next/link";

interface FeedbackStats {
  total: number;
  by_source_type: Record<string, number>;
  by_vehicle_model: Record<string, number>;
  by_market: Record<string, number>;
  by_language: Record<string, number>;
}

interface FeedbackItem {
  id: string;
  text: string;
  source_type: string;
  language: string;
  timestamp: string;
  vehicle_model: string;
  market: string;
}

function StatCard({
  title,
  value,
  icon,
  color = "blue",
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: string;
}) {
  return (
    <Paper withBorder p="md" radius="md">
      <Group justify="space-between">
        <div>
          <Text size="xs" c="dimmed" tt="uppercase" fw={700}>
            {title}
          </Text>
          <Text fw={700} size="xl">
            {value}
          </Text>
        </div>
        <Paper
          p="xs"
          radius="md"
          style={{ backgroundColor: `var(--mantine-color-${color}-light)` }}
        >
          {icon}
        </Paper>
      </Group>
    </Paper>
  );
}

const sourceTypeIcons: Record<string, React.ReactNode> = {
  voice: <IconMicrophone size={16} />,
  touch: <IconHandFinger size={16} />,
  error: <IconAlertTriangle size={16} />,
};

const sourceTypeColors: Record<string, string> = {
  voice: "blue",
  touch: "green",
  error: "red",
};

export default function Dashboard() {
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [feedbacks, setFeedbacks] = useState<FeedbackItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsRes, feedbacksRes] = await Promise.all([
          fetch("http://localhost:8000/api/feedbacks/stats"),
          fetch("http://localhost:8000/api/feedbacks/?limit=10"),
        ]);

        if (statsRes.ok) {
          setStats(await statsRes.json());
        }
        if (feedbacksRes.ok) {
          setFeedbacks(await feedbacksRes.json());
        }
      } catch (error) {
        console.error("Failed to fetch data:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

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
        Dashboard
      </Title>

      {/* KPI-Karten */}
      <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} mb="xl">
        <StatCard
          title="Feedbacks Gesamt"
          value={stats?.total ?? 0}
          icon={<IconMessage size={24} color="var(--mantine-color-blue-6)" />}
          color="blue"
        />
        <StatCard
          title="Sprachassistent"
          value={stats?.by_source_type?.voice ?? 0}
          icon={<IconMicrophone size={24} color="var(--mantine-color-violet-6)" />}
          color="violet"
        />
        <StatCard
          title="Touch-Events"
          value={stats?.by_source_type?.touch ?? 0}
          icon={<IconHandFinger size={24} color="var(--mantine-color-green-6)" />}
          color="green"
        />
        <StatCard
          title="Fehlermeldungen"
          value={stats?.by_source_type?.error ?? 0}
          icon={<IconAlertTriangle size={24} color="var(--mantine-color-red-6)" />}
          color="red"
        />
      </SimpleGrid>

      <Grid>
        {/* Nach Fahrzeugmodell */}
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Paper withBorder p="lg" radius="md" h="100%">
            <Group mb="md">
              <IconCar size={20} />
              <Text size="lg" fw={500}>
                Nach Fahrzeugmodell
              </Text>
            </Group>
            {stats?.by_vehicle_model &&
              Object.entries(stats.by_vehicle_model)
                .sort((a, b) => b[1] - a[1])
                .map(([model, count]) => (
                  <Group key={model} justify="space-between" mb="xs">
                    <Text size="sm">{model || "Unbekannt"}</Text>
                    <Badge variant="light">{count}</Badge>
                  </Group>
                ))}
          </Paper>
        </Grid.Col>

        {/* Nach Markt */}
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Paper withBorder p="lg" radius="md" h="100%">
            <Group mb="md">
              <IconWorld size={20} />
              <Text size="lg" fw={500}>
                Nach Markt
              </Text>
            </Group>
            {stats?.by_market &&
              Object.entries(stats.by_market)
                .sort((a, b) => b[1] - a[1])
                .map(([market, count]) => (
                  <Group key={market} justify="space-between" mb="xs">
                    <Text size="sm">{market || "Unbekannt"}</Text>
                    <Badge variant="light" color="teal">
                      {count}
                    </Badge>
                  </Group>
                ))}
          </Paper>
        </Grid.Col>

        {/* Quellen-Verteilung - Modern */}
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Paper withBorder p="lg" radius="md" h="100%" style={{ background: 'linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%)' }}>
            <Text size="lg" fw={500} mb="lg">
              Quellen-Verteilung
            </Text>
            <Stack gap="md">
              {/* Voice */}
              <div>
                <Group justify="space-between" mb={4}>
                  <Group gap="xs">
                    <div style={{ width: 12, height: 12, borderRadius: '50%', background: 'linear-gradient(135deg, #7c3aed 0%, #a855f7 100%)' }} />
                    <Text size="sm" fw={500}>Sprache</Text>
                  </Group>
                  <Text size="sm" fw={700} c="violet">{stats?.by_source_type?.voice ?? 0}</Text>
                </Group>
                <div style={{ height: 8, background: '#e9ecef', borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{
                    width: `${((stats?.by_source_type?.voice ?? 0) / (stats?.total || 1)) * 100}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #7c3aed 0%, #a855f7 100%)',
                    borderRadius: 4,
                    transition: 'width 0.5s ease'
                  }} />
                </div>
              </div>
              {/* Touch */}
              <div>
                <Group justify="space-between" mb={4}>
                  <Group gap="xs">
                    <div style={{ width: 12, height: 12, borderRadius: '50%', background: 'linear-gradient(135deg, #059669 0%, #34d399 100%)' }} />
                    <Text size="sm" fw={500}>Touch</Text>
                  </Group>
                  <Text size="sm" fw={700} c="green">{stats?.by_source_type?.touch ?? 0}</Text>
                </Group>
                <div style={{ height: 8, background: '#e9ecef', borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{
                    width: `${((stats?.by_source_type?.touch ?? 0) / (stats?.total || 1)) * 100}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #059669 0%, #34d399 100%)',
                    borderRadius: 4,
                    transition: 'width 0.5s ease'
                  }} />
                </div>
              </div>
              {/* Error */}
              <div>
                <Group justify="space-between" mb={4}>
                  <Group gap="xs">
                    <div style={{ width: 12, height: 12, borderRadius: '50%', background: 'linear-gradient(135deg, #dc2626 0%, #f87171 100%)' }} />
                    <Text size="sm" fw={500}>Fehler</Text>
                  </Group>
                  <Text size="sm" fw={700} c="red">{stats?.by_source_type?.error ?? 0}</Text>
                </Group>
                <div style={{ height: 8, background: '#e9ecef', borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{
                    width: `${((stats?.by_source_type?.error ?? 0) / (stats?.total || 1)) * 100}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #dc2626 0%, #f87171 100%)',
                    borderRadius: 4,
                    transition: 'width 0.5s ease'
                  }} />
                </div>
              </div>
              {/* Total */}
              <Paper p="sm" radius="md" mt="xs" style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%)' }}>
                <Group justify="center" gap="xs">
                  <Text size="xl" fw={700} c="white">{stats?.total ?? 0}</Text>
                  <Text size="sm" c="white" opacity={0.8}>Feedbacks gesamt</Text>
                </Group>
              </Paper>
            </Stack>
          </Paper>
        </Grid.Col>

        {/* Top-Probleme / Quick Insights */}
        <Grid.Col span={12}>
          <Paper withBorder p="lg" radius="md" style={{ background: 'linear-gradient(135deg, #667eea11 0%, #764ba211 100%)' }}>
            <Group mb="md">
              <IconAlertTriangle size={24} color="var(--mantine-color-orange-6)" />
              <Text size="lg" fw={600}>
                Top-Probleme erkannt
              </Text>
              <Badge color="orange" variant="light" size="lg">KI-Analyse</Badge>
            </Group>
            <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }}>
              {(() => {
                // Analyse der häufigsten Probleme aus Feedbacks
                const problemKeywords: Record<string, { count: number; models: Set<string> }> = {};
                const keywords = ['Sprachassistent', 'Navigation', 'Bluetooth', 'Update', 'Touch', 'Display', 'Klimaanlage', 'CarPlay', 'Android Auto'];

                feedbacks.forEach((fb) => {
                  keywords.forEach((kw) => {
                    if (fb.text.toLowerCase().includes(kw.toLowerCase())) {
                      if (!problemKeywords[kw]) {
                        problemKeywords[kw] = { count: 0, models: new Set() };
                      }
                      problemKeywords[kw].count++;
                      if (fb.vehicle_model) problemKeywords[kw].models.add(fb.vehicle_model);
                    }
                  });
                });

                const topProblems = Object.entries(problemKeywords)
                  .filter(([, data]) => data.count > 0)
                  .sort((a, b) => b[1].count - a[1].count)
                  .slice(0, 4);

                return topProblems.map(([keyword, data]) => (
                  <Anchor
                    key={keyword}
                    component={Link}
                    href={`/feedbacks?search=${encodeURIComponent(keyword)}`}
                    underline="never"
                    style={{ display: 'block' }}
                  >
                    <Paper p="md" radius="md" withBorder style={{ cursor: 'pointer', transition: 'all 0.2s' }} className="problem-card">
                      <Text size="sm" c="dimmed" mb={4}>Problem-Thema</Text>
                      <Text fw={600} size="lg" mb={4}>{keyword}</Text>
                      <Group gap="xs">
                        <Badge color="red" variant="filled">{data.count} Meldungen</Badge>
                        <Badge color="blue" variant="light">{[...data.models].slice(0, 2).join(', ') || 'Alle Modelle'}</Badge>
                      </Group>
                    </Paper>
                  </Anchor>
                ));
              })()}
            </SimpleGrid>
          </Paper>
        </Grid.Col>

        {/* Letzte Feedbacks */}
        <Grid.Col span={12}>
          <Paper withBorder p="lg" radius="md">
            <Text size="lg" fw={500} mb="md">
              Letzte Feedbacks
            </Text>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>ID</Table.Th>
                  <Table.Th>Typ</Table.Th>
                  <Table.Th>Modell</Table.Th>
                  <Table.Th>Markt</Table.Th>
                  <Table.Th>Feedback</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {feedbacks.map((fb) => (
                  <Table.Tr key={fb.id}>
                    <Table.Td>
                      <Anchor component={Link} href={`/feedback/${fb.id}`} size="sm">
                        {fb.id}
                      </Anchor>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        size="sm"
                        color={sourceTypeColors[fb.source_type] || "gray"}
                        leftSection={sourceTypeIcons[fb.source_type]}
                      >
                        {fb.source_type}
                      </Badge>
                    </Table.Td>
                    <Table.Td>{fb.vehicle_model || "-"}</Table.Td>
                    <Table.Td>{fb.market || "-"}</Table.Td>
                    <Table.Td>
                      <Text size="sm" lineClamp={1}>
                        {fb.text}
                      </Text>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Paper>
        </Grid.Col>
      </Grid>
    </Container>
  );
}
