# Shell Completion for asyncdev

Generated for Platform Phase 4: Unified Platform Shell.

## Installation

### Bash

Copy the completion script to your bash completion directory:

```bash
# System-wide (requires sudo)
sudo cp asyncdev.bash /usr/share/bash-completion/completions/asyncdev

# User-specific
mkdir -p ~/.bash_completion
cp asyncdev.bash ~/.bash_completion/asyncdev
```

Or source it directly in your `.bashrc`:

```bash
echo 'source /path/to/amazing-async-dev/cli/completion/asyncdev.bash' >> ~/.bashrc
```

### Zsh

Copy the completion script to your zsh completion directory:

```bash
# System-wide (requires sudo)
sudo cp asyncdev.zsh /usr/share/zsh/site-functions/_asyncdev

# User-specific
mkdir -p ~/.zsh/completions
cp asyncdev.zsh ~/.zsh/completions/_asyncdev
```

Or add to your `.zshrc`:

```bash
fpath=(~/.zsh/completions $fpath)
autoload -Uz _asyncdev
compdef _asyncdev asyncdev
```

## Usage

After installation, press Tab to complete commands and options:

```bash
asyncdev <TAB>           # Shows all commands
asyncdev home <TAB>      # Shows home subcommands
asyncdev recovery <TAB>  # Shows recovery subcommands
asyncdev --project <TAB> # Shows project choices
```

## Features

- Command completion for all 40+ asyncdev commands
- Subcommand completion for: recovery, decision, observe-runs, acceptance, evidence, home
- Option completion for: --project, --path, --execution, --feature, --status
- Value completion for: --policy, --decision
