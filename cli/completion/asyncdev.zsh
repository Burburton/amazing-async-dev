#compdef asyncdev

_asyncdev() {
    local -a commands
    commands=(
        'status:Show current RunState status'
        'version:Show version'
        'init:Initialize project structure'
        'new-product:Create new product'
        'new-feature:Create new feature'
        'plan-day:Plan today'\''s bounded task'
        'run-day:Run today'\''s execution'
        'review-night:Generate nightly review pack'
        'resume-next-day:Resume from decisions'
        'complete-feature:Mark feature as completed'
        'archive-feature:Archive completed feature'
        'backfill:Backfill historical features'
        'archive:Query archived features'
        'summary:Management summary'
        'feedback:Record workflow feedback'
        'policy:Execution policy configuration'
        'email-decision:Async decision channel'
        'notification:Notification management'
        'snapshot:Workspace snapshot'
        'doctor:Diagnose workspace health'
        'journal:View loop artifact timeline'
        'gmail-auth:Gmail OAuth2 setup'
        'resend-auth:Resend email setup'
        'check-inbox:Check pending decisions'
        'config:Config safety commands'
        'project-link:Project-link management'
        'browser-test:Browser verification'
        'frontend-verify-run:Frontend verification'
        'sqlite:SQLite state queries'
        'inspect-stop:Inspect stop point'
        'recovery:Recovery Console'
        'decision:Decision Inbox'
        'session-start:Session start check'
        'verification:Verification Console'
        'observe-runs:Execution Observer'
        'acceptance:Acceptance Console'
        'evidence:Evidence Summary'
        'home:Operator Home'
    )

    local -a recovery_cmds
    recovery_cmds=('list:List recovery items' 'show:Show recovery details' 'resume:Resume recovery')

    local -a decision_cmds
    decision_cmds=('list:List decisions' 'show:Show decision' 'reply:Reply to decision' 'wait:Wait for decision' 'history:Decision history')

    local -a observe_cmds
    observe_cmds=('run:Run observation' 'status:Observer status' 'types:Observer types')

    local -a acceptance_cmds
    acceptance_cmds=('run:Run acceptance' 'status:Acceptance status' 'history:Acceptance history' 'result:Acceptance result' 'retry:Retry acceptance' 'recovery:Acceptance recovery' 'gate:Acceptance gate')

    local -a evidence_cmds
    evidence_cmds=('summary:Evidence summary' 'latest:Latest evidence' 'generate:Generate evidence' 'questions:Evidence questions')

    local -a home_cmds
    home_cmds=('show:Show home overview' 'status:Home status' 'calm:Check if calm')

    local -a project_opts
    project_opts=('--project:Filter by project ID' '--path:Projects root path' '--help:Show help')

    local -a policy_modes
    policy_modes=('always_trigger:Always trigger acceptance' 'feature_completion_only:On feature completion' 'manual_only:Manual only')

    local -a decision_opts
    decision_opts=('approve:Approve' 'revise:Revise' 'defer:Defer')

    _arguments -C \
        '1: :->command' \
        '2: :->subcommand' \
        '3: :->subsubcommand' \
        '*:: :->args'

    case $state in
        command)
            _describe 'command' commands
            ;;
        subcommand)
            case ${words[2]} in
                recovery)
                    _describe 'recovery command' recovery_cmds
                    ;;
                decision)
                    _describe 'decision command' decision_cmds
                    ;;
                observe-runs)
                    _describe 'observe-runs command' observe_cmds
                    ;;
                acceptance)
                    _describe 'acceptance command' acceptance_cmds
                    ;;
                evidence)
                    _describe 'evidence command' evidence_cmds
                    ;;
                home)
                    _describe 'home command' home_cmds
                    ;;
                *)
                    _arguments "${project_opts[@]}"
                    ;;
            esac
            ;;
        subsubcommand)
            case "${words[2]},${words[3]}" in
                recovery,list|recovery,show|recovery,resume)
                    _arguments "${project_opts[@]}" '--all:Show all projects'
                    ;;
                decision,list|decision,show|decision,reply|decision,wait|decision,history)
                    _arguments "${project_opts[@]}" '--all:Show all projects' '--status:Filter by status'
                    ;;
                observe-runs,run|observe-runs,status|observe-runs,types)
                    _arguments "${project_opts[@]}" '--all:Observe all projects'
                    ;;
                acceptance,run|acceptance,status|acceptance,history|acceptance,result|acceptance,retry|acceptance,recovery|acceptance,gate)
                    _arguments '--project:Project ID' '--execution:Execution ID' '--feature:Feature ID' '--policy:Policy mode:(${policy_modes})' '--dry-run:Preview only' '--path:Projects path'
                    ;;
                evidence,summary|evidence,latest|evidence,generate|evidence,questions)
                    _arguments "${project_opts[@]}" '--feature:Feature ID' '--save:Save to file'
                    ;;
                home,show|home,status|home,calm)
                    _arguments "${project_opts[@]}"
                    ;;
            esac
            ;;
        args)
            case ${words[CURRENT-1]} in
                --project|--path|--execution|--feature)
                    _files
                    ;;
                --status)
                    _values 'status' 'pending' 'sent' 'resolved'
                    ;;
                --policy)
                    _values 'policy' "${policy_modes[@]}"
                    ;;
                --decision)
                    _values 'decision' "${decision_opts[@]}"
                    ;;
            esac
            ;;
    esac
}

_asyncdev "$@"
