# AgendaFácil

Agenda de atendimentos de uma clínica pequena: marca, remarca e lista
atendimentos mantidos em memória.
Projeto da Unidade 1 de DIM0501 - Boas Práticas de Programação (DIMAp/UFRN) -
refatoração, documentação e defensividade aplicadas sobre o código-base
`agenda_base.py`.

## Integrantes

| Nome                     | Matrícula   |
| ------------------------ | ----------- |
| Luiz Carlos Victor Pinto | 20250024456 |

## Requisitos

- Python 3.10 ou superior
- Apenas biblioteca padrão para rodar `agendafacil.py` - nenhuma
  dependência externa no código
- `pdoc` é usado só para gerar a documentação em `docs/` (ver seção
  abaixo); não é importado nem necessário para executar o programa

## Como executar

O arquivo principal é `agendafacil.py`. Ele reproduz a mesma demonstração do
código-base: marca três atendimentos (um em conflito de horário), remarca um
deles e lista o dia.

```bash
python3 agendafacil.py
```

Saída esperada:

```
Atendimento marcado para Ana
Horario ocupado
Atendimento marcado para Carla
Remarcado
14 Carla Dra. Souza MARCADO
```

## Estrutura do repositório

```
agendafacil.py   Código refatorado, documentado e defensivo
RELATORIO.md     Diagnóstico e decisões de projeto
docs/            Documentação de API gerada
```

## Como gerar a documentação de API

A documentação já pronta está em `docs/agendafacil.html`. Ela foi gerada com
`pdoc`, que é a única dependência do projeto e serve só para gerar essa
documentação (o código de `agendafacil.py` continua usando apenas a
biblioteca padrão, como pede o projeto).

## Regras de negócio implementadas

| Regra      | Definição                                                                 |
| ---------- | ------------------------------------------------------------------------- |
| Expediente | Atendimentos só podem começar entre 8h e 17h; o último termina até as 18h |
| Duração    | Entre 15 e 120 minutos, em múltiplos de 15                                |
| Conflito   | Um profissional não pode ter dois atendimentos no mesmo dia e horário     |
| Data       | Formato AAAA-MM-DD; qualquer outro formato é entrada inválida             |

Entrada inválida em qualquer uma dessas regras levanta `ValueError` (ou
`HorarioIndisponivelError`/`AtendimentoNaoEncontradoError`, exceções próprias
do módulo) com uma mensagem dizendo o que está errado e qual valor causou o
problema. Nenhum erro é engolido em silêncio.

## Diagnóstico e decisões de projeto

Ver [`RELATORIO.md`](RELATORIO.md) para a tabela de diagnóstico do
código-base (19 anomalias, cinco categorias) e a justificativa de cada
decisão tomada na refatoração.
