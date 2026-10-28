# RELATORIO - Projeto da Unidade 1 - AgendaFácil

DIM0501 - Boas Práticas de Programação · DIMAp/UFRN

## Etapa 1 — Diagnóstico do código-base (`agenda_base.py`)

Mínimo de dez anomalias, com ao menos uma por categoria.

### 1. Adequação e lógica

| #   | Anomalia (e onde)                                                                                                                                     | Por que é um problema                                                                                                     |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| 1   | `add()` só checa `h < 18` para o início; não verifica se o atendimento **termina** até as 18h (ex.: `h=17, dur=120` seria aceito e terminaria às 19h) | Viola a regra de negócio real do expediente; gera atendimentos que extrapolam o horário da clínica sem nenhum aviso       |
| 2   | `add()` só exige `dur > 0`; não há limite superior nem exigência de múltiplo de 15 min                                                                | Permite durações absurdas (ex.: 100000 minutos) e durações que não encaixam no "bloco" de agenda da recepção              |
| 3   | Nenhuma validação do formato da data em `d` (string livre)                                                                                            | Datas como `"05/10/2026"` ou `"ontem"` são aceitas e armazenadas, quebrando qualquer comparação/ordenação futura por data |
| 4   | `rem()` quando paciente/data/hora não batem com nenhum atendimento simplesmente não faz nada, sem print nem erro                                      | Falha silenciosa: quem chamou acha que remarcou e não remarcou nada                                                       |

### 2. Manutenibilidade

| #   | Anomalia (e onde)                                                                                                         | Por que é um problema                                                                                     |
| --- | ------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| 5   | Cabeçalho com histórico de autores e datas de alteração no topo do arquivo                                                | Informação que já é responsabilidade do `git log`/`git blame`; só desatualiza com o tempo                 |
| 6   | Nomes curtos e não descritivos em toda parte: `add`, `rem`, `lst`, `p`, `pr`, `d`, `h`, `dur`, `nd`, `nh`, `ok`, `a`, `b` | Ninguém entende o que a função faz ou o que cada parâmetro representa sem ler o corpo inteiro             |
| 7   | A verificação de conflito de horário está duplicada: um laço em `add()` e outro, ligeiramente diferente, em `rem()`       | Qualquer mudança na regra de conflito precisa ser replicada nos dois lugares, e é fácil esquecer um deles |
| 8   | `# TODO: rever isso depois (Joao, 2025)` sem dizer o quê rever, por quê, nem ter responsável ativo                        | TODO vago e vencido não orienta ninguém a agir                                                            |

### 3. Organização e estética

| #   | Anomalia (e onde)                                                                                                                         | Por que é um problema                                                                                      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| 9   | `add()` acumula três responsabilidades: valida entrada, decide conflito e imprime o resultado                                             | Dificulta testar e reutilizar qualquer uma das partes isoladamente                                         |
| 10  | Pirâmide de `if`s aninhados em `add()` (`if h>=8: if h<18: if dur>0: ...`) em vez de cláusulas de guarda                                  | Cada nível de indentação some com a legibilidade e esconde o caminho de erro                               |
| 11  | Atendimento representado como lista posicional `[p, pr, d, h, dur, "MARCADO"]`, acessada por índices mágicos (`a[0]`, `a[1]`, ... `a[5]`) | Trocar a ordem dos campos quebra tudo em silêncio; ninguém sabe o que `a[3]` significa sem contar posições |
| 12  | Valores mágicos soltos no código: `8`, `18`, `"MARCADO"`                                                                                  | Repetidos em vários lugares sem nome, não dá para saber se `18` é "hora de fechamento" só de olhar         |
| 13  | Código morto comentado (`# def desmarcar(p, d, h): # ag.remove(...)`)                                                                     | Não executa, não é testado e faz o leitor perder tempo tentando entender por que está ali                  |

### 4. Programação defensiva e segurança

| #   | Anomalia (e onde)                                                                                  | Por que é um problema                                                                                      |
| --- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| 14  | `try: ... except: pass` genérico envolvendo toda a lógica de `add()`                               | Qualquer erro (ex.: `h` recebido como string) é engolido; a função nem agenda, nem avisa, nem deixa rastro |
| 15  | Nenhuma validação de tipos em `add()` nem `rem()` (`p`, `pr` podem ser `None`; `h` pode ser texto) | Combinado com o `except: pass`, qualquer entrada malformada vira um "nada aconteceu" sem explicação        |
| 16  | `rem()` não tem nenhum tratamento de erro nem validação de pré-condição                            | Um `d`/`h` de tipo errado estoura uma exceção não tratada direto no chamador, sem contexto do que causou   |
| 17  | `lst()` não valida `d`                                                                             | Passar `None` ou um tipo inesperado simplesmente não lista nada, sem indicar que a consulta falhou         |

### 5. Desempenho e recursos

| #   | Anomalia (e onde)                                                                                                                                                             | Por que é um problema                                                                                                          |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 18  | O laço de verificação de conflito em `add()` e em `rem()` sempre percorre a lista inteira, mesmo depois de já ter encontrado um conflito (`ok = False`), por não usar `break` | Trabalho desnecessário a cada chamada; irrelevante com poucos registros, mas escala mal                                        |
| 19  | `rem()` faz uma busca aninhada O(n²) (`for a in ag: ... for b in ag: ...`) para cada remarcação                                                                               | Mesma observação: aceitável no volume atual de uma clínica pequena, mas é uma dívida técnica a registrar, não a resolver agora |

**Total: 19 anomalias registradas**, cobrindo as cinco categorias (mínimo de 10 exigido).

---

## Etapa 2 - Decisões de refatoração

- **Uma responsabilidade por função.** `Agenda.marcar()` e `Agenda.remarcar()` só validam e alteram o estado, nunca imprimem. A impressão ficou isolada em `_marcar_e_informar()`, `_remarcar_e_informar()` e `_listar_e_imprimir()`, que só existem para a demonstração de linha de comando. Isso resolve a anomalia #9.
- **Conflito de horário em um único lugar.** Criei `existe_conflito_de_horario()`, usada tanto por `marcar()` quanto por `remarcar()` (com o parâmetro `ignorar` para o atendimento remarcado não conflitar consigo mesmo). Resolve a anomalia #7 e, por extensão, a duplicação de laços de desempenho (#18, #19 ficaram concentradas num só lugar, mais fácil de otimizar no futuro se necessário).
- **Atendimento como tipo nomeado.** `Atendimento` é uma `dataclass` com campos `paciente`, `profissional`, `data`, `hora`, `duracao_minutos`, `status`. Resolve a anomalia #11 (acesso por índice).
- **Constantes nomeadas.** `HORA_ABERTURA_EXPEDIENTE`, `HORA_FECHAMENTO_EXPEDIENTE`, `DURACAO_MINIMA_MINUTOS`, `DURACAO_MAXIMA_MINUTOS`, `MULTIPLO_DURACAO_MINUTOS`, `STATUS_MARCADO`. Resolve a anomalia #12.
- **Nomenclatura PEP 8.** Funções e variáveis em `snake_case` com nomes descritivos (`marcar`, `remarcar`, `listar_do_dia`, `validar_data`, `existe_conflito_de_horario`...), classes em `PascalCase` (`Agenda`, `Atendimento`, `HorarioIndisponivelError`), constantes em `MAIUSCULAS_COM_UNDERSCORE`. Resolve a anomalia #6.
- **Caminho feliz preservado.** `diff` entre a saída de `agenda_base.py` e de `agendafacil.py` para o cenário de demonstração é vazio, as duas imprimem exatamente:
    ```
    Atendimento marcado para Ana
    Horario ocupado
    Atendimento marcado para Carla
    Remarcado
    14 Carla Dra. Souza MARCADO
    ```

## Etapa 3 — Decisões de documentação

- Toda função e método público recebeu docstring no estilo Google (Sphinx), com `Args`, `Returns` e `Raises` quando aplicável.
- O cabeçalho de histórico de autores, os comentários de ruído (`# adiciona na lista`, `# remarca o atendimento`, etc.), o código morto (`# def desmarcar...`) e o TODO vencido foram removidos (resolvem as anomalias #5, #13, #8).
- Comentário de decisão (porquê que o código não revela sozinho): no topo do módulo, explico de onde vêm os valores de expediente (8h–18h, horário do prédio alugado) e de múltiplo de duração (15 min, forma como a recepção organiza encaixes). É uma justificativa de negócio inventada para fins do exercício.
- Documentação de API gerada com `pydoc` (biblioteca padrão) em `docs/agendafacil.html`, ver comando no README. Não foi possível instalar `pdoc` neste ambiente (`pip install pdoc` falhou por ser um ambiente Python gerenciado externamente, `externally-managed-environment`); o README documenta esse comando como alternativa para quem tiver `pdoc` disponível.

## Etapa 4 — Decisões de programação defensiva

Mudança de propósito registrada conforme exigido: **o comportamento para entradas inválidas deixou de ser "ignorar em silêncio" e passou a ser "falhar explicitamente"**. Only o caminho feliz permanece idêntico; qualquer script externo que dependesse do silêncio antigo (ex.: chamar `add()` com hora 20h e esperar que nada acontecesse sem erro) vai agora receber uma exceção.

- **Pré-condições com cláusulas de guarda.** `validar_texto_obrigatorio`, `validar_data`, `validar_duracao_minutos` e `validar_hora_do_atendimento` são chamadas no início de `marcar()`/`remarcar()`, antes de qualquer efeito colateral.
- **Exceções específicas com mensagem e valor causador.** `ValueError` para dado inválido (sempre citando o valor recebido), e duas exceções próprias: `HorarioIndisponivelError` (conflito de horário) e `AtendimentoNaoEncontradoError` (remarcar algo que não existe).
- **Nenhum bloco de captura vazio ou genérico.** O `try/except: pass` de `add()` foi eliminado. Os únicos `try/except` que restam (em `_marcar_e_informar`/`_remarcar_e_informar`) capturam apenas `HorarioIndisponivelError`, nunca `Exception` genérica, e sempre produzem uma saída visível.
- **Nenhuma falha silenciosa.** Marcar às 20h agora lança `ValueError` (antes, não fazia nada). Remarcar um atendimento inexistente agora lança `AtendimentoNaoEncontradoError` (antes, não fazia nada).
- **Regras de negócio implementadas:**
    - _Expediente_: início entre 8h e 17h, término calculado (`hora + duracao/60`) deve ser ≤ 18h.
    - _Duração_: entre 15 e 120 minutos, múltiplo de 15.
    - _Conflito_: verificado em `existe_conflito_de_horario()`, único lugar.
    - _Data_: validada com `datetime.strptime(data, "%Y-%m-%d")`.

## Dívidas técnicas assumidas (não resolvidas nesta entrega)

- **Desempenho (#18, #19):** a verificação de conflito continua sendo uma busca linear/O(n²) na lista de atendimentos. Para o volume de uma clínica pequena isso é irrelevante; se o volume crescer, a estrutura correta seria um índice (dicionário) por `(profissional, data, hora)`.
- **Status do atendimento** continua sendo uma string simples (`STATUS_MARCADO`) em vez de um `Enum`; foi uma escolha para manter o escopo pequeno, já que a regra de negócio não pede mais de um status hoje.

## Uso de ferramentas de IA

Este trabalho foi desenvolvido com apoio do Claude Code para apoio com a documentação, tirar dúvidas com o refatoramento do código e geração deste relatório.
