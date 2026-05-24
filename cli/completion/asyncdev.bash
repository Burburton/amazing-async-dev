# bash completion for asyncdev
# Generated for Platform Phase 4: Unified Platform Shell

_asyncdev_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Main commands
    commands="status version init new-product new-feature plan-day run-day review-night resume-next-day complete-feature archive-feature backfill archive summary feedback policy email-decision notification snapshot doctor journal gmail-auth resend-auth check-inbox config project-link browser-test frontend-verify-run sqlite inspect-stop recovery decision session-start verification observe-runs acceptance evidence home"

    # Commands with --project option
    project_commands="recovery decision observe-runs acceptance evidence home snapshot doctor summary feedback journal"

    # Commands with subcommands
    subcommand_commands="init new-product new-feature plan-day run-day review-night resume-next-day complete-feature archive-feature backfill archive summary feedback policy email-decision notification snapshot doctor journal gmail-auth resend-auth check-inbox config project-link browser-test frontend-verify-run sqlite inspect-stop recovery decision session-start verification observe-runs acceptance evidence home"

    # If we're completing a command
    if [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=($(compgen -W "${commands}" -- "${cur}"))
        return 0
    fi

    # If the previous word is a command that takes --project
    if [[ " ${project_commands} " =~ " ${prev} " ]]; then
        case "${prev}" in
            recovery)
                if [[ ${COMP_CWORD} -eq 2 ]]; then
                    subcommands="list show resume"
                    COMPREPLY=($(compgen -W "${subcommands}" -- "${cur}"))
                elif [[ ${COMP_CWORD} -eq 3 && "${COMP_WORDS[COMP_CWORD-2]}" == "list" ]]; then
                    COMPREPLY=($(compgen -W "--project --all --path --help" -- "${cur}"))
                elif [[ ${COMP_CWORD} -eq 3 && "${COMP_WORDS[COMP_CWORD-2]}" == "show" ]]; then
                    COMPREPLY=($(compgen -W "--project --path --help" -- "${cur}"))
                elif [[ ${COMP_CWORD} -eq 3 && "${COMP_WORDS[COMP_CWORD-2]}" == "resume" ]]; then
                    COMPREPLY=($(compgen -W "--project --path --help" -- "${cur}"))
                fi
                ;;
            decision)
                if [[ ${COMP_CWORD} -eq 2 ]]; then
                    subcommands="list show reply wait history"
                    COMPREPLY=($(compgen -W "${subcommands}" -- "${cur}"))
                else
                    COMPREPLY=($(compgen -W "--project --all --status --path --help" -- "${cur}"))
                fi
                ;;
            observe-runs)
                if [[ ${COMP_CWORD} -eq 2 ]]; then
                    subcommands="run status types"
                    COMPREPLY=($(compgen -W "${subcommands}" -- "${cur}"))
                else
                    COMPREPLY=($(compgen -W "--project --all --path --help" -- "${cur}"))
                fi
                ;;
            acceptance)
                if [[ ${COMP_CWORD} -eq 2 ]]; then
                    subcommands="run status history result retry recovery gate"
                    COMPREPLY=($(compgen -W "${subcommands}" -- "${cur}"))
                else
                    COMPREPLY=($(compgen -W "--project --execution --feature --policy --dry-run --path --help" -- "${cur}"))
                fi
                ;;
            evidence)
                if [[ ${COMP_CWORD} -eq 2 ]]; then
                    subcommands="summary latest generate questions"
                    COMPREPLY=($(compgen -W "${subcommands}" -- "${cur}"))
                else
                    COMPREPLY=($(compgen -W "--project --feature --path --save --help" -- "${cur}"))
                fi
                ;;
            home)
                if [[ ${COMP_CWORD} -eq 2 ]]; then
                    subcommands="show status calm"
                    COMPREPLY=($(compgen -W "${subcommands}" -- "${cur}"))
                else
                    COMPREPLY=($(compgen -W "--project --path --help" -- "${cur}"))
                fi
                ;;
            *)
                COMPREPLY=($(compgen -W "--project --help" -- "${cur}"))
                ;;
        esac
        return 0
    fi

    # Generic options for completion
    case "${prev}" in
        --project|--path|--execution|--feature|--status)
            return 0
            ;;
        --policy)
            COMPREPLY=($(compgen -W "always_trigger feature_completion_only manual_only" -- "${cur}"))
            return 0
            ;;
        --mode)
            COMPREPLY=($(compgen -W "external live mock" -- "${cur}"))
            return 0
            ;;
        --decision)
            COMPREPLY=($(compgen -W "approve revise defer" -- "${cur}"))
            return 0
            ;;
        --help|-h)
            return 0
            ;;
    esac

    # Default completion
    COMPREPLY=($(compgen -W "--help" -- "${cur}"))
    return 0
}

complete -F _asyncdev_completion asyncdev
complete -F _asyncdev_completion python
complete -F _asyncdev_completion -o default
