"use client";

import {
    AppShell,
    Burger,
    Flex,
    Group,
    NavLink,
    ScrollArea,
    Text,
    ThemeIcon,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import {
    IconChartBar,
    IconFileExport,
    IconMessageCircle,
    IconUpload,
    IconDashboard,
    IconSettings,
    IconList,
    IconFlask,
} from "@tabler/icons-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

interface NavItem {
    icon: React.ElementType;
    label: string;
    href: string;
}

const mainLinks: NavItem[] = [
    { icon: IconDashboard, label: "Dashboard", href: "/" },
    { icon: IconList, label: "Feedbacks", href: "/feedbacks" },
    { icon: IconMessageCircle, label: "Chat", href: "/chat" },
    { icon: IconUpload, label: "Ingest", href: "/ingest" },
    { icon: IconChartBar, label: "Analytics", href: "/analytics" },
    { icon: IconFlask, label: "Evaluation", href: "/evaluation" },
    { icon: IconFileExport, label: "Export", href: "/export" },
];

const settingsLinks: NavItem[] = [
    { icon: IconSettings, label: "Einstellungen", href: "/settings" },
];

function NavItem({ item }: { item: NavItem }) {
    const path = usePathname();
    const Icon = item.icon;

    return (
        <NavLink
            active={path === item.href}
            href={item.href}
            label={item.label}
            leftSection={<Icon size={20} />}
            component={Link}
            styles={{
                root: { borderRadius: 8 },
            }}
        />
    );
}

export default function MainContainer({
    children,
}: Readonly<{ children: ReactNode }>) {
    const [opened, { toggle }] = useDisclosure();

    return (
        <AppShell
            header={{ height: 60 }}
            navbar={{
                width: 280,
                breakpoint: "sm",
                collapsed: { mobile: !opened },
            }}
            padding="md"
        >
            <AppShell.Header>
                <Flex h="100%" px="md" align="center" justify="space-between">
                    <Group>
                        <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
                        <ThemeIcon size="lg" variant="gradient" gradient={{ from: "blue", to: "cyan" }}>
                            <IconMessageCircle size={24} />
                        </ThemeIcon>
                        <Text fw={700} size="lg">
                            Feedback-Copilot
                        </Text>
                    </Group>
                    <Text size="sm" c="dimmed">
                        VW In-Car Feedback Analysis
                    </Text>
                </Flex>
            </AppShell.Header>

            <AppShell.Navbar p="sm" component={ScrollArea}>
                <AppShell.Section>
                    <Text size="xs" fw={500} c="dimmed" mb="xs">
                        NAVIGATION
                    </Text>
                    {mainLinks.map((item) => (
                        <NavItem key={item.href} item={item} />
                    ))}
                </AppShell.Section>

                <AppShell.Section mt="xl">
                    <Text size="xs" fw={500} c="dimmed" mb="xs">
                        EINSTELLUNGEN
                    </Text>
                    {settingsLinks.map((item) => (
                        <NavItem key={item.href} item={item} />
                    ))}
                </AppShell.Section>
            </AppShell.Navbar>

            <AppShell.Main>{children}</AppShell.Main>
        </AppShell>
    );
}
