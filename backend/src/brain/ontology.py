from pydantic import BaseModel, Field

# ====================================
# ENTITY TYPES
# ====================================

class Person(BaseModel):
    """A specific, named human who works at or with the company.
 
    Examples: "Priya Raman", "the new backend hire Marcus".
 
    NOT a role or a group. "The on-call engineer" is a Role, not a Person.
    "The platform team" is a Team, not a Person. Only extract a Person when
    an actual individual is identified.
    """

    role: str | None = Field(
        default = None,
        description = "Their job title as written in the source, e.g. 'Staff Engineer', 'Head of Sales'."
    )
    team_name: str | None = Field(
        default = None,
        description = "The team they belong to, as written in the source."
    )

class Team(BaseModel):
    """A durable, named group of people inside the company.
 
    Examples: "Platform", "Growth", "Customer Success", "the data team".
 
    NOT a temporary working group formed for one project (that is a Project),
    and not the company as a whole.
    """

    function: str | None = Field(
        default=None,
        description="Broad area the team works in, e.g. 'engineering', 'sales', 'operations'.",
    )
    parent_team: str | None = Field(
        default=None,
        description="The larger team or department this one sits inside, if stated.",
    )

class Project(BaseModel):
    """A time-bounded effort with a start, an intended end, and a goal.
 
    Examples: "Billing v2", "the SOC 2 audit", "Q3 onboarding revamp".
 
    NOT something the company operates permanently. If the thing still exists
    and needs maintaining after the work stops, it is a System. A project
    BUILDS a system; it is not the system.
    """
 
    status: str | None = Field(
        default=None,
        description="Current state as stated in the source, e.g. 'planned', 'in progress', 'shipped', 'cancelled'.",
    )
    target_date: str | None = Field(
        default=None,
        description="Stated deadline or target completion date, copied verbatim from the source.",
    )

class System(BaseModel):
    """Something the company builds, runs, and maintains itself.
 
    Examples: "the billing service", "the iOS app", "the events pipeline", "the internal admin dashboard".
 
    The test that separates this from Tool: WE BUILD AND OPERATE Systems.
    WE BUY OR ADOPT Tools. If the company would have to fix it themselves when
    it breaks, it is a System.
    """
 
    kind: str | None = Field(
        default=None,
        description="What sort of thing it is, e.g. 'service', 'web app', 'data pipeline', 'database', 'library'.",
    )
    lifecycle_status: str | None = Field(
        default=None,
        description="Stated lifecycle state, e.g. 'planned', 'active', 'deprecated', 'decommissioned'.",
    )

class Tool(BaseModel):
    """Third-party software, service, or vendor product the company uses.
 
    Examples: "Datadog", "Salesforce", "Postgres", "Figma", "Stripe".
 
    The test that separates this from System: WE BUY OR ADOPT Tools. WE BUILD
    Systems. A tool is made by someone else.
 
    Statements of the form "we use X for Y" are the most common and most
    valuable facts in a company workspace, because they get replaced often —
    which is exactly what the temporal graph is for.
    """
 
    category: str | None = Field(
        default=None,
        description="What it is used for, e.g. 'monitoring', 'CRM', 'database', 'design', 'payments'.",
    )
    vendor: str | None = Field(
        default=None,
        description="The company that makes it, if different from the tool name.",
    )

class Process(BaseModel):
    """A repeatable procedure describing HOW the company does something.
 
    Examples: "the deploy process", "expense reimbursement", "how to request
    a laptop", "the incident escalation runbook", "weekly sprint planning".
 
    NOT a rule about what is allowed (that is a Policy) and not a one-time
    effort (that is a Project). A Process answers "how do I do X?".
    """
 
    trigger: str | None = Field(
        default=None,
        description="What causes this process to start, e.g. 'a new hire joins', 'a P1 incident is declared'.",
    )
    cadence: str | None = Field(
        default=None,
        description="How often it runs, if it is scheduled, e.g. 'weekly', 'per release', 'as needed'.",
    )
    owner_team: str | None = Field(
        default=None,
        description="The team responsible for the process, as stated.",
    )

class Policy(BaseModel):
    """A rule that constrains behaviour and is currently in force.
 
    Examples: "the PTO policy", "no production access without 2FA",
    "all expenses over $500 need VP approval", "the remote work policy".
 
    NOT a description of how to do something (that is a Process) and not a
    one-off choice (that is a Decision). A Policy answers "what am I allowed
    to do?" and generally applies to a group of people over time.
 
    Supersede, never overwrite: when a policy changes, the old one should stay
    in the graph with its validity window closed.
    """
 
    scope: str | None = Field(
        default=None,
        description="Who or what the policy applies to, e.g. 'all employees', 'engineering only', 'US contractors'.",
    )
    enforcement: str | None = Field(
        default=None,
        description="How binding it is, e.g. 'mandatory', 'recommended', 'guideline'.",
    )

class Decision(BaseModel):
    """A specific choice made between alternatives at a point in time.
 
    Examples: "we chose ClickHouse over Postgres for analytics", "we decided
    to delay the launch to October", "we agreed to drop IE11 support".
 
    NOT every statement of fact. A Decision requires that something else could
    plausibly have been chosen instead. "The billing service is written in Go"
    is a fact about a System. "We decided to rewrite billing in Go" is a
    Decision.
 
    The rejected alternatives matter as much as the choice — "why didn't we
    use X?" is a question nobody can normally answer.
    """
 
    rationale: str | None = Field(
        default=None,
        description="The stated reason the choice was made. Copy the reasoning given in the source.",
    )
    alternatives_considered: str | None = Field(
        default=None,
        description="Other options that were weighed and not chosen, if the source names them.",
    )
    decided_on: str | None = Field(
        default=None,
        description="The date the decision was made, copied verbatim from the source if stated.",
    )

class Metric(BaseModel):
    """A named quantity the company tracks, targets, or reports on.
 
    Examples: "weekly active users", "gross margin", "p95 latency",
    "trial-to-paid conversion", "Q3 revenue target".
 
    NOT a one-off number mentioned in passing. A Metric is something measured
    repeatedly. Targets change every planning cycle, which makes these
    naturally temporal.
    """
 
    unit: str | None = Field(
        default=None,
        description="What it is measured in, e.g. 'USD', 'percent', 'milliseconds', 'users'.",
    )
    target_value: str | None = Field(
        default=None,
        description="The goal for this metric, copied verbatim, e.g. '15% MoM', '$2.4M ARR'.",
    )
    current_value: str | None = Field(
        default=None,
        description="The most recent reported value, copied verbatim.",
    )
    period: str | None = Field(
        default=None,
        description="The time period the target or value refers to, e.g. 'Q3 2026', 'FY26'.",
    )

class Meeting(BaseModel):
    """A specific occasion on which people gathered to discuss something.
 
    Examples: "the March 4 architecture review", "weekly eng sync",
    "the Acme QBR".
 
    IMPORTANT: the meeting is the real-world event, NOT the notes document
    about it. The document is already stored separately as the source. Extract
    a Meeting so that decisions and action items can be traced back to the room
    they came out of.
    """
 
    purpose: str | None = Field(
        default=None,
        description="What the meeting was for, e.g. 'architecture review', 'quarterly planning'.",
    )
    cadence: str | None = Field(
        default=None,
        description="How often it recurs, if it is a standing meeting, e.g. 'weekly', 'monthly'.",
    )
    occurred_on: str | None = Field(
        default=None,
        description="The date it took place, copied verbatim from the source.",
    )

class Initiative(BaseModel):
    """A large, multi-project push toward a business objective.
 
    Examples: "the enterprise readiness initiative", "H2 international
    expansion", "the reliability push".
 
    The layer ABOVE Project. An Initiative contains several projects, is
    usually sponsored by leadership, and has no single deliverable of its own.
 
    NOT a Project. The test: if it has one deliverable and one owner, it is a
    Project. If it is an umbrella that other efforts sit under, it is an
    Initiative. If in doubt, prefer Project — Initiative is the rarer thing.
    """
 
    status: str | None = Field(
        default=None,
        description="Stated state, e.g. 'proposed', 'active', 'paused', 'complete'.",
    )
    time_horizon: str | None = Field(
        default=None,
        description="The period it spans, copied verbatim, e.g. 'FY26', 'H2 2026', 'next 18 months'.",
    )
    objective: str | None = Field(
        default=None,
        description="The business outcome it is meant to achieve, as stated.",
    )

class Requirement(BaseModel):
    """Something a product or system is supposed to do.
 
    Covers features, capabilities, user stories, acceptance criteria, and
    explicit asks. Examples: "support SSO login", "the app should work
    offline", "exports must complete in under 30 seconds", "dark mode".
 
    NOT the work of building it (that is a Project) and not the thing that
    ends up built (that is a System). A Requirement is the stated need or
    capability itself.
 
    Requirements get revised constantly — an earlier spec saying one thing and
    a later one saying another is a superseding pair worth capturing.
    """
 
    status: str | None = Field(
        default=None,
        description="Stated state, e.g. 'proposed', 'accepted', 'built', 'descoped'.",
    )
    priority: str | None = Field(
        default=None,
        description="Stated priority, copied verbatim, e.g. 'P0', 'must-have', 'nice to have'.",
    )
    acceptance_criteria: str | None = Field(
        default=None,
        description="How the source says you would know it is satisfied.",
    )

class ActionItem(BaseModel):
    """A specific commitment by a specific party to do a specific thing.
 
    Examples: "Priya to update the runbook by Friday", "eng to spike on the
    caching approach", "follow up with legal about the DPA".
 
    NOT a Project (much smaller, usually one person and days at most), and not
    a Requirement (that is what the product should do; this is what a person
    committed to do). Meeting notes are full of these.
 
    Only extract one when there is a real commitment. A statement of intent
    with no owner and no verb of commitment is usually just discussion.
    """
 
    status: str | None = Field(
        default=None,
        description="Stated state, e.g. 'open', 'in progress', 'done', 'dropped'.",
    )
    due: str | None = Field(
        default=None,
        description="Stated deadline, copied verbatim, e.g. 'by Friday', '2026-09-01', 'before launch'.",
    )

class OpenQuestion(BaseModel):
    """Something the company has explicitly not decided yet.
 
    Examples: "do we build or buy the search index?", "open question: which
    region do we launch in first?", "TBD: pricing for the enterprise tier".
 
    NOT a Decision — it is the *absence* of one. The moment it is answered, a
    Decision should Resolve it, which closes this node's validity window. That
    open-then-closed arc is one of the clearest demonstrations of what a
    temporal graph does that plain search cannot.
 
    NOT a Risk either: a Risk is something that might go wrong; an
    OpenQuestion is something nobody has chosen yet.
    """
 
    status: str | None = Field(
        default=None,
        description="Stated state, e.g. 'open', 'answered', 'deferred'.",
    )
    context: str | None = Field(
        default=None,
        description="Why the question matters or what is waiting on it, as stated.",
    )

class Risk(BaseModel):
    """A named thing that might go wrong, flagged in advance.
 
    Examples: "the vendor may not deliver before Q4", "single point of failure
    in the auth service", "key-person risk on the billing rewrite".
 
    NOT a problem that has already happened (that is an incident) and not an
    undecided choice (that is an OpenQuestion). A Risk is prospective — it has
    not occurred yet, and something is usually being done to reduce it.
    """
 
    likelihood: str | None = Field(
        default=None,
        description="How likely it is, as stated, e.g. 'high', 'unlikely', '30%'.",
    )
    impact: str | None = Field(
        default=None,
        description="What happens if it materialises, as stated.",
    )
    status: str | None = Field(
        default=None,
        description="Stated state, e.g. 'open', 'mitigated', 'accepted', 'closed'.",
    )

class Term(BaseModel):
    """A word, acronym, or phrase with a company-specific meaning.
 
    Examples: "DRI", "EPS", "the golden path", "T2 account", "north star
    metric".
 
    This is the one type a general-purpose model genuinely cannot resolve on
    its own: internal jargon looks like ordinary language but means something
    only this company knows. Definitions also drift, and two teams often define
    the same acronym differently — which is exactly what Contradicts is for.
 
    NOT an industry-standard term any reader would already know. Extract a Term
    when the source is defining or explaining vocabulary, or when a phrase is
    clearly being used as internal shorthand.
    """
 
    expansion: str | None = Field(
        default=None,
        description="What the acronym or abbreviation stands for, if it is one.",
    )
    definition: str | None = Field(
        default=None,
        description="The meaning as given in the source. Copy the wording used.",
    )
    domain: str | None = Field(
        default=None,
        description="Which part of the company uses it, if the source says.",
    )

# ==================================
# EDGE TYPES
# ==================================

class MemberOf(BaseModel):
    """A person belongs to a team."""
 
    role_on_team: str | None = Field(
        default=None,
        description="What they do on that team, if stated, e.g. 'tech lead', 'designer'.",
    )

class ReportsTo(BaseModel):
    """A person's manager. Reorganisations make this change often."""
 
    line_kind: str | None = Field(
        default=None,
        description="'direct' for a normal reporting line, 'dotted' for a secondary or matrixed one.",
    )

class Owns(BaseModel):
    """The person or team accountable for something.
 
    Use for the party who decides about it and is responsible when it breaks —
    not merely someone who worked on it once.
    """
 
    ownership_kind: str | None = Field(
        default=None,
        description="The flavour of ownership, e.g. 'DRI', 'maintainer', 'sponsor', 'approver'.",
    )

class ExpertIn(BaseModel):
    """A person is a recognised go-to for a system, process, or topic.
 
    This is the "who should I ask about X?" edge. Only extract it when the
    source actually points at someone, e.g. "ask Priya about the events
    pipeline", "Marcus owns all the Terraform knowledge".
    """
 
    basis: str | None = Field(
        default=None,
        description="Why they are the expert, as stated, e.g. 'wrote the original service'.",
    )

class Uses(BaseModel):
    """A team, project, or system relies on a tool in its day-to-day work.
 
    Statements like "we use Datadog for monitoring". These get replaced often,
    so the validity window on this edge carries a lot of the product's value.
    """
 
    purpose: str | None = Field(
        default=None,
        description="What it is used for, as stated, e.g. 'monitoring', 'analytics', 'deployments'.",
    )

class DependsOn(BaseModel):
    """One thing will not work correctly without another.
 
    A technical or operational dependency, not a preference.
    """
 
    dependency_kind: str | None = Field(
        default=None,
        description="Nature of the dependency, e.g. 'runtime', 'data', 'build', 'operational'.",
    )
    criticality: str | None = Field(
        default=None,
        description="How severe the impact is if the dependency fails, if stated.",
    )

class BlockedBy(BaseModel):
    """Work cannot proceed until something else is resolved."""
 
    reason: str | None = Field(
        default=None,
        description="Why it is blocked, as stated in the source.",
    )

class PartOf(BaseModel):
    """A containment or hierarchy relationship.
 
    A project inside a larger initiative, a sub-team inside a department, a
    component inside a larger system.
    """

class Supersedes(BaseModel):
    """The newer thing replaces the older thing of the same kind.
 
    This is the most important edge in the graph. Use it when one policy,
    process, decision, tool, target, or system explicitly takes the place of
    another. The old one is not deleted — its validity window closes.
 
    Direction is always NEW -> OLD. "ClickHouse supersedes Postgres for
    analytics", not the reverse.
    """
 
    reason: str | None = Field(
        default=None,
        description="Why the replacement happened, as stated in the source.",
    )

class Contradicts(BaseModel):
    """Two sources disagree, and neither is clearly the successor to the other.
 
    Different from Supersedes: with Supersedes there is a winner. Here there
    is an unresolved conflict — two live documents state incompatible things.
    Surfacing these is more useful than silently picking one.
    """
 
    field_in_conflict: str | None = Field(
        default=None,
        description="What specifically the two disagree about, e.g. 'the approval threshold', 'the launch date'.",
    )
    severity: str | None = Field(
        default=None,
        description="How consequential the disagreement is, if it can be judged from the source.",
    )

class AppliesTo(BaseModel):
    """A policy, process, or decision governs some group or thing.
 
    This is the scope edge. Without it, "which policies affect my team?" has
    no answer.
    """
 
    exceptions: str | None = Field(
        default=None,
        description="Any stated carve-outs or exemptions.",
    )

class DecidedBy(BaseModel):
    """The person or team who made or approved a decision."""
 
    decision_role: str | None = Field(
        default=None,
        description="Their part in it, e.g. 'proposed', 'approved', 'final sign-off'.",
    )

class Rejected(BaseModel):
    """An alternative that was explicitly considered and NOT chosen.
 
    Design docs and RFCs are full of these and almost nobody indexes them.
    This edge is what lets an agent answer "why didn't we go with X?".
    """
 
    reason: str | None = Field(
        default=None,
        description="Why it was ruled out, as stated in the source.",
    )

class Measures(BaseModel):
    """A metric tracks the performance of a team, project, or system."""

class Attended(BaseModel):
    """A person was present at a meeting."""
 
    participation: str | None = Field(
        default=None,
        description="Their part in it, e.g. 'organizer', 'presenter', 'attendee'.",
    )

class AssignedTo(BaseModel):
    """An action item or open question has a named party responsible for it.
 
    Distinct from Owns: Owns is standing accountability for a durable thing.
    AssignedTo is a one-off task landing on someone's plate.
    """

class ArisesFrom(BaseModel):
    """This came out of that.
 
    A decision, action item, risk, or question that originated in a particular
    meeting, decision, or discussion. This is the provenance-of-reasoning edge:
    it is what lets an agent say *"that was decided in the March 4 architecture
    review"* rather than just naming a document.
    """

class Resolves(BaseModel):
    """A decision or action item answers an open question.
 
    Direction is ANSWER -> QUESTION.
 
    This is the edge that closes an OpenQuestion's validity window. Extract it
    whenever a source settles something that was previously listed as
    undecided, even if the two are in different documents.
    """
 
    resolution: str | None = Field(
        default=None,
        description="What the answer turned out to be, as stated.",
    )

class Threatens(BaseModel):
    """A risk endangers a project, initiative, system, metric, or requirement."""
 
    impact: str | None = Field(
        default=None,
        description="The stated consequence if the risk materialises.",
    )

class MitigatedBy(BaseModel):
    """A risk is reduced by a process, decision, project, or action item.
 
    Direction is RISK -> MITIGATION.
    """
 
    mitigation: str | None = Field(
        default=None,
        description="How the mitigation works, as stated.",
    )

class RefersTo(BaseModel):
    """A term or an open question is about a specific, concrete thing.
 
    Two uses. First, connecting internal jargon to what it actually names:
    "EPS" -> the events pipeline System. Second, connecting an open question to
    the thing it concerns.
 
    Keep this narrow. It is NOT a general-purpose "these are related" edge — if
    a more specific edge type fits, use that instead.
    """

class RequestedBy(BaseModel):
    """A requirement was asked for by a particular person or team."""
 
    reason: str | None = Field(
        default=None,
        description="Why they asked for it, as stated.",
    )

# ===========================
# REGISTRIES
# ===========================

ENTITY_TYPES = {
    "Person": Person,
    "Team": Team,
    "Initiative": Initiative,
    "Project": Project,
    "System": System,
    "Tool": Tool,
    "Process": Process,
    "Policy": Policy,
    "Decision": Decision,
    "Requirement": Requirement,
    "ActionItem": ActionItem,
    "OpenQuestion": OpenQuestion,
    "Risk": Risk,
    "Metric": Metric,
    "Meeting": Meeting,
    "Term": Term,
}
 
EDGE_TYPES = {
    "MemberOf": MemberOf,
    "ReportsTo": ReportsTo,
    "Owns": Owns,
    "ExpertIn": ExpertIn,
    "Uses": Uses,
    "DependsOn": DependsOn,
    "BlockedBy": BlockedBy,
    "PartOf": PartOf,
    "Supersedes": Supersedes,
    "Contradicts": Contradicts,
    "AppliesTo": AppliesTo,
    "DecidedBy": DecidedBy,
    "Rejected": Rejected,
    "Measures": Measures,
    "Attended": Attended,
    "AssignedTo": AssignedTo,
    "ArisesFrom": ArisesFrom,
    "Resolves": Resolves,
    "Threatens": Threatens,
    "MitigatedBy": MitigatedBy,
    "RefersTo": RefersTo,
    "RequestedBy": RequestedBy,
}

# ======================================
# RELATIONSHIP MAP
# ======================================
EDGE_TYPE_MAP = {
    # --- people and org structure ---
    ("Person", "Team"): ["MemberOf"],
    ("Person", "Person"): ["ReportsTo"],
    ("Team", "Team"): ["PartOf"],
    ("Person", "Meeting"): ["Attended"],
    # --- ownership and expertise ---
    ("Person", "Project"): ["Owns"],
    ("Person", "Initiative"): ["Owns"],
    ("Person", "System"): ["Owns", "ExpertIn"],
    ("Person", "Process"): ["Owns", "ExpertIn"],
    ("Person", "Policy"): ["Owns"],
    ("Person", "Tool"): ["ExpertIn"],
    ("Person", "Term"): ["ExpertIn"],
    ("Team", "Project"): ["Owns"],
    ("Team", "Initiative"): ["Owns"],
    ("Team", "System"): ["Owns"],
    ("Team", "Process"): ["Owns"],
    ("Team", "Metric"): ["Owns"],
    ("Team", "Risk"): ["Owns"],
    # --- what runs on what ---
    ("Team", "Tool"): ["Uses"],
    ("Project", "Tool"): ["Uses"],
    ("Process", "Tool"): ["Uses"],
    ("System", "Tool"): ["Uses", "DependsOn"],
    ("System", "System"): ["DependsOn", "PartOf", "Supersedes"],
    # --- work in flight ---
    ("Project", "Project"): ["BlockedBy", "PartOf", "DependsOn"],
    ("Project", "Initiative"): ["PartOf"],
    ("Project", "System"): ["BlockedBy"],
    ("Project", "Decision"): ["BlockedBy"],
    ("Project", "OpenQuestion"): ["BlockedBy"],
    ("Initiative", "Initiative"): ["Supersedes", "PartOf"],
    # --- replacement and conflict (the temporal core) ---
    ("Policy", "Policy"): ["Supersedes", "Contradicts"],
    ("Process", "Process"): ["Supersedes", "Contradicts"],
    ("Decision", "Decision"): ["Supersedes", "Contradicts"],
    ("Tool", "Tool"): ["Supersedes"],
    ("Metric", "Metric"): ["Supersedes", "Contradicts"],
    ("Term", "Term"): ["Supersedes", "Contradicts"],
    ("Requirement", "Requirement"): ["Supersedes", "BlockedBy"],
    # --- scope: who does a rule bind? ---
    ("Policy", "Team"): ["AppliesTo"],
    ("Policy", "Project"): ["AppliesTo"],
    ("Policy", "Initiative"): ["AppliesTo"],
    ("Policy", "System"): ["AppliesTo"],
    ("Policy", "Person"): ["AppliesTo"],
    ("Process", "Team"): ["AppliesTo"],
    ("Process", "System"): ["AppliesTo"],
    ("Decision", "Team"): ["DecidedBy", "AppliesTo"],
    ("Decision", "Project"): ["AppliesTo"],
    ("Decision", "Initiative"): ["AppliesTo"],
    # --- decisions, their alternatives, and where they came from ---
    ("Decision", "Person"): ["DecidedBy"],
    ("Decision", "Tool"): ["Rejected"],
    ("Decision", "System"): ["AppliesTo", "Rejected"],
    ("Decision", "Meeting"): ["ArisesFrom"],
    ("Decision", "OpenQuestion"): ["Resolves"],
    # --- measurement ---
    ("Metric", "Team"): ["Measures"],
    ("Metric", "Project"): ["Measures"],
    ("Metric", "Initiative"): ["Measures"],
    ("Metric", "System"): ["Measures"],
    # --- requirements ---
    ("Requirement", "Project"): ["PartOf"],
    ("Requirement", "Initiative"): ["PartOf"],
    ("Requirement", "Person"): ["RequestedBy"],
    ("Requirement", "Team"): ["RequestedBy"],
    ("Requirement", "System"): ["DependsOn"],
    ("Requirement", "OpenQuestion"): ["BlockedBy"],
    # --- action items ---
    ("ActionItem", "Person"): ["AssignedTo"],
    ("ActionItem", "Team"): ["AssignedTo"],
    ("ActionItem", "Project"): ["PartOf"],
    ("ActionItem", "Meeting"): ["ArisesFrom"],
    ("ActionItem", "Decision"): ["ArisesFrom"],
    ("ActionItem", "OpenQuestion"): ["Resolves"],
    ("ActionItem", "ActionItem"): ["BlockedBy"],
    # --- open questions ---
    ("OpenQuestion", "Person"): ["AssignedTo"],
    ("OpenQuestion", "Project"): ["RefersTo"],
    ("OpenQuestion", "System"): ["RefersTo"],
    ("OpenQuestion", "Meeting"): ["ArisesFrom"],
    # --- risks ---
    ("Risk", "Project"): ["Threatens"],
    ("Risk", "Initiative"): ["Threatens"],
    ("Risk", "System"): ["Threatens"],
    ("Risk", "Metric"): ["Threatens"],
    ("Risk", "Requirement"): ["Threatens"],
    ("Risk", "Process"): ["MitigatedBy"],
    ("Risk", "Decision"): ["MitigatedBy"],
    ("Risk", "ActionItem"): ["MitigatedBy"],
    ("Risk", "Meeting"): ["ArisesFrom"],
    # --- glossary terms: connect jargon to the thing it names ---
    ("Term", "System"): ["RefersTo"],
    ("Term", "Tool"): ["RefersTo"],
    ("Term", "Team"): ["RefersTo"],
    ("Term", "Process"): ["RefersTo"],
    ("Term", "Project"): ["RefersTo"],
    ("Term", "Metric"): ["RefersTo"],
}