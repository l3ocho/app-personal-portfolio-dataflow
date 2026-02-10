"""Contact page - Form UI and direct contact information."""

import dash
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

dash.register_page(__name__, path="/contact", name="Contact")

# Contact information
CONTACT_INFO = {
    "email": "leobrmi@hotmail.com",
    "phone": "(416) 859-7936",
    "linkedin": "https://www.linkedin.com/in/leobmiranda/",
    "github": "https://github.com/l3ocho",
    "location": "Toronto, ON, Canada",
}

# Page intro text
INTRO_TEXT = (
    "I'm currently open to Senior Data Analyst and Data Engineer roles in Toronto "
    "(or remote). If you're working on something interesting and need someone who can "
    "build data infrastructure from scratch, I'd like to hear about it."
)

CONSULTING_TEXT = (
    "For consulting inquiries (automation, dashboards, small business data work), "
    "reach out about Bandit Labs."
)

# Form subject options
SUBJECT_OPTIONS = [
    {"value": "job", "label": "Job Opportunity"},
    {"value": "consulting", "label": "Consulting Inquiry"},
    {"value": "other", "label": "Other"},
]


def create_intro_section() -> dmc.Stack:
    """Create the intro text section."""
    return dmc.Stack(
        [
            dmc.Title("Get In Touch", order=1, ta="center"),
            dmc.Text(INTRO_TEXT, size="md", ta="center", maw=600, mx="auto"),
            dmc.Text(
                CONSULTING_TEXT, size="md", ta="center", maw=600, mx="auto", c="dimmed"
            ),
        ],
        gap="md",
        mb="xl",
    )


def create_contact_form() -> dmc.Paper:
    """Create the contact form with Formspree integration."""
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Title("Send a Message", order=2, size="h4"),
                # Feedback container for success/error messages
                html.Div(id="contact-feedback"),
                dmc.TextInput(
                    id="contact-name",
                    label="Name",
                    placeholder="Your name",
                    leftSection=DashIconify(icon="tabler:user", width=18),
                    required=True,
                ),
                dmc.TextInput(
                    id="contact-email",
                    label="Email",
                    placeholder="your.email@example.com",
                    leftSection=DashIconify(icon="tabler:mail", width=18),
                    required=True,
                ),
                dmc.Select(
                    id="contact-subject",
                    label="Subject",
                    placeholder="Select a subject",
                    data=SUBJECT_OPTIONS,
                    leftSection=DashIconify(icon="tabler:tag", width=18),
                ),
                dmc.Textarea(
                    id="contact-message",
                    label="Message",
                    placeholder="Your message...",
                    minRows=4,
                    required=True,
                ),
                # Honeypot field for spam protection (hidden from users)
                dmc.TextInput(
                    id="contact-gotcha",
                    style={"position": "absolute", "left": "-9999px"},
                    tabIndex=-1,
                    autoComplete="off",
                ),
                dmc.Button(
                    "Send Message",
                    id="contact-submit",
                    fullWidth=True,
                    leftSection=DashIconify(icon="tabler:send", width=18),
                ),
            ],
            gap="md",
            style={"position": "relative"},
        ),
        p="xl",
        radius="md",
        withBorder=True,
    )


def create_direct_contact() -> dmc.Paper:
    """Create the direct contact information section."""
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Title("Direct Contact", order=2, size="h4"),
                dmc.Stack(
                    [
                        # Email
                        dmc.Group(
                            [
                                dmc.ThemeIcon(
                                    DashIconify(icon="tabler:mail", width=20),
                                    size="lg",
                                    radius="md",
                                    variant="light",
                                ),
                                dmc.Stack(
                                    [
                                        dmc.Text("Email", size="sm", c="dimmed"),
                                        dmc.Anchor(
                                            CONTACT_INFO["email"],
                                            href=f"mailto:{CONTACT_INFO['email']}",
                                            size="md",
                                            fw=500,
                                        ),
                                    ],
                                    gap=0,
                                ),
                            ],
                            gap="md",
                        ),
                        # Phone
                        dmc.Group(
                            [
                                dmc.ThemeIcon(
                                    DashIconify(icon="tabler:phone", width=20),
                                    size="lg",
                                    radius="md",
                                    variant="light",
                                ),
                                dmc.Stack(
                                    [
                                        dmc.Text("Phone", size="sm", c="dimmed"),
                                        dmc.Anchor(
                                            CONTACT_INFO["phone"],
                                            href=f"tel:{CONTACT_INFO['phone'].replace('(', '').replace(')', '').replace(' ', '').replace('-', '')}",
                                            size="md",
                                            fw=500,
                                        ),
                                    ],
                                    gap=0,
                                ),
                            ],
                            gap="md",
                        ),
                        # LinkedIn
                        dmc.Group(
                            [
                                dmc.ThemeIcon(
                                    DashIconify(icon="tabler:brand-linkedin", width=20),
                                    size="lg",
                                    radius="md",
                                    variant="light",
                                    color="blue",
                                ),
                                dmc.Stack(
                                    [
                                        dmc.Text("LinkedIn", size="sm", c="dimmed"),
                                        dmc.Anchor(
                                            "linkedin.com/in/leobmiranda",
                                            href=CONTACT_INFO["linkedin"],
                                            target="_blank",
                                            size="md",
                                            fw=500,
                                        ),
                                    ],
                                    gap=0,
                                ),
                            ],
                            gap="md",
                        ),
                        # GitHub
                        dmc.Group(
                            [
                                dmc.ThemeIcon(
                                    DashIconify(icon="tabler:brand-github", width=20),
                                    size="lg",
                                    radius="md",
                                    variant="light",
                                ),
                                dmc.Stack(
                                    [
                                        dmc.Text("GitHub", size="sm", c="dimmed"),
                                        dmc.Anchor(
                                            "github.com/l3ocho",
                                            href=CONTACT_INFO["github"],
                                            target="_blank",
                                            size="md",
                                            fw=500,
                                        ),
                                    ],
                                    gap=0,
                                ),
                            ],
                            gap="md",
                        ),
                    ],
                    gap="lg",
                ),
            ],
            gap="lg",
        ),
        p="xl",
        radius="md",
        withBorder=True,
    )


def create_location_section() -> dmc.Paper:
    """Create the location and work eligibility section."""
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Title("Location", order=2, size="h4"),
                dmc.Group(
                    [
                        dmc.ThemeIcon(
                            DashIconify(icon="tabler:map-pin", width=20),
                            size="lg",
                            radius="md",
                            variant="light",
                            color="red",
                        ),
                        dmc.Stack(
                            [
                                dmc.Text(CONTACT_INFO["location"], size="md", fw=500),
                                dmc.Text(
                                    "Canadian Citizen | Eligible to work in Canada and US",
                                    size="sm",
                                    c="dimmed",
                                ),
                            ],
                            gap=0,
                        ),
                    ],
                    gap="md",
                ),
            ],
            gap="md",
        ),
        p="xl",
        radius="md",
        withBorder=True,
    )


layout = dmc.Container(
    dmc.Stack(
        [
            create_intro_section(),
            dmc.SimpleGrid(
                [
                    create_contact_form(),
                    dmc.Stack(
                        [
                            create_direct_contact(),
                            create_location_section(),
                        ],
                        gap="lg",
                    ),
                ],
                cols={"base": 1, "md": 2},
                spacing="xl",
            ),
            dmc.Space(h=40),
        ],
        gap="lg",
    ),
    size="lg",
    py="xl",
)
