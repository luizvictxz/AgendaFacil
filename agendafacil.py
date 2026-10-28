from dataclasses import dataclass, field
from datetime import datetime

HORA_ABERTURA_EXPEDIENTE = 8
HORA_FECHAMENTO_EXPEDIENTE = 18
DURACAO_MINIMA_MINUTOS = 15
DURACAO_MAXIMA_MINUTOS = 120
MULTIPLO_DURACAO_MINUTOS = 15
FORMATO_DATA = "%Y-%m-%d"
STATUS_MARCADO = "MARCADO"


class HorarioIndisponivelError(Exception):
    """Levantada quando o profissional ja tem outro atendimento no mesmo
    dia e horario."""


class AtendimentoNaoEncontradoError(Exception):
    """Levantada quando nao existe atendimento com os dados informados para
    ser remarcado."""


@dataclass
class Atendimento:
    """Um atendimento marcado na agenda.

    Args:
        paciente (str): Nome do paciente atendido.
        profissional (str): Nome do profissional responsavel.
        data (str): Data do atendimento, no formato AAAA-MM-DD.
        hora (int): Hora de inicio do atendimento (0-23).
        duracao_minutos (int): Duracao do atendimento, em minutos.
        status (str): Situacao atual do atendimento. Padrao: STATUS_MARCADO.
    """

    paciente: str
    profissional: str
    data: str
    hora: int
    duracao_minutos: int
    status: str = field(default=STATUS_MARCADO)


def validar_texto_obrigatorio(valor, rotulo):
    """Garante que o valor e uma string nao vazia.

    Args:
        valor: Valor recebido para validacao.
        rotulo (str): Nome do campo, usado na mensagem de erro.

    Raises:
        ValueError: Se ``valor`` nao for uma string ou estiver em branco.
    """
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(
            f"{rotulo} deve ser um texto nao vazio, mas veio {valor!r}")


def validar_data(data):
    """Garante que a data esta no formato AAAA-MM-DD.

    Args:
        data (str): Data a validar.

    Raises:
        ValueError: Se ``data`` nao for uma string no formato AAAA-MM-DD.
    """
    validar_texto_obrigatorio(data, "data")
    try:
        datetime.strptime(data, FORMATO_DATA)
    except ValueError as erro:
        raise ValueError(
            f"data deve estar no formato AAAA-MM-DD, mas veio {data!r}"
        ) from erro


def validar_duracao_minutos(duracao_minutos):
    """Garante que a duracao esta dentro da faixa e dos multiplos aceitos.

    Args:
        duracao_minutos (int): Duracao do atendimento, em minutos.

    Raises:
        ValueError: Se ``duracao_minutos`` nao for um inteiro entre
            DURACAO_MINIMA_MINUTOS e DURACAO_MAXIMA_MINUTOS, multiplo de
            MULTIPLO_DURACAO_MINUTOS.
    """
    if isinstance(
            duracao_minutos, bool) or not isinstance(
            duracao_minutos, int):
        raise ValueError(
            f"duracao_minutos deve ser um numero inteiro, mas veio {duracao_minutos!r}"
        )
    if not DURACAO_MINIMA_MINUTOS <= duracao_minutos <= DURACAO_MAXIMA_MINUTOS:
        raise ValueError(
            f"duracao_minutos deve estar entre {DURACAO_MINIMA_MINUTOS} e "
            f"{DURACAO_MAXIMA_MINUTOS}, mas veio {duracao_minutos!r}"
        )
    if duracao_minutos % MULTIPLO_DURACAO_MINUTOS != 0:
        raise ValueError(
            f"duracao_minutos deve ser multiplo de {MULTIPLO_DURACAO_MINUTOS}, "
            f"mas veio {duracao_minutos!r}"
        )


def validar_hora_do_atendimento(hora, duracao_minutos):
    """Garante que o atendimento comeca e termina dentro do expediente.

    Args:
        hora (int): Hora de inicio do atendimento (0-23).
        duracao_minutos (int): Duracao do atendimento, em minutos, ja
            validada por validar_duracao_minutos.

    Raises:
        ValueError: Se ``hora`` nao for um inteiro, se o atendimento comecar
            fora do expediente ou se terminar depois do fechamento.
    """
    if isinstance(hora, bool) or not isinstance(hora, int):
        raise ValueError(f"hora deve ser um numero inteiro, mas veio {hora!r}")
    if not HORA_ABERTURA_EXPEDIENTE <= hora < HORA_FECHAMENTO_EXPEDIENTE:
        raise ValueError(
            f"hora deve estar entre {HORA_ABERTURA_EXPEDIENTE} e "
            f"{HORA_FECHAMENTO_EXPEDIENTE - 1}, mas veio {hora!r}"
        )
    hora_de_termino = hora + duracao_minutos / 60
    if hora_de_termino > HORA_FECHAMENTO_EXPEDIENTE:
        raise ValueError(
            f"atendimento das {hora}h com duracao de {duracao_minutos} min "
            f"terminaria as {hora_de_termino}h, depois do fechamento as "
            f"{HORA_FECHAMENTO_EXPEDIENTE}h"
        )


def existe_conflito_de_horario(
        atendimentos, profissional, data, hora, ignorar=None):
    """Verifica se um profissional ja tem atendimento no mesmo dia e horario.

    Esta e a unica funcao do modulo que decide sobre conflito de horario;
    marcar_atendimento e remarcar_atendimento delegam a ela.

    Args:
        atendimentos (list[Atendimento]): Atendimentos ja marcados.
        profissional (str): Profissional a verificar.
        data (str): Data a verificar, no formato AAAA-MM-DD.
        hora (int): Hora a verificar.
        ignorar (Atendimento | None): Atendimento a ignorar na verificacao
            (usado ao remarcar um atendimento contra ele mesmo).

    Returns:
        bool: True se ja existir outro atendimento do mesmo profissional no
        mesmo dia e horario, False caso contrario.
    """
    for atendimento in atendimentos:
        if atendimento is ignorar:
            continue
        if (
            atendimento.profissional == profissional
            and atendimento.data == data
            and atendimento.hora == hora
        ):
            return True
    return False


class Agenda:
    """Agenda de atendimentos mantida em memoria.

    Encapsula a lista de atendimentos e garante que toda alteracao passa
    pelas mesmas validacoes e pela mesma verificacao de conflito.
    """

    def __init__(self):
        self._atendimentos = []

    def marcar(self, paciente, profissional, data, hora, duracao_minutos):
        """Marca um novo atendimento.

        Args:
            paciente (str): Nome do paciente.
            profissional (str): Nome do profissional.
            data (str): Data do atendimento, no formato AAAA-MM-DD.
            hora (int): Hora de inicio do atendimento.
            duracao_minutos (int): Duracao do atendimento, em minutos.

        Returns:
            Atendimento: O atendimento recem-criado.

        Raises:
            ValueError: Se algum dado for invalido (ver funcoes de
                validacao deste modulo).
            HorarioIndisponivelError: Se o profissional ja tiver outro
                atendimento no mesmo dia e horario.
        """
        validar_texto_obrigatorio(paciente, "paciente")
        validar_texto_obrigatorio(profissional, "profissional")
        validar_data(data)
        validar_duracao_minutos(duracao_minutos)
        validar_hora_do_atendimento(hora, duracao_minutos)

        if existe_conflito_de_horario(
                self._atendimentos, profissional, data, hora):
            raise HorarioIndisponivelError(
                f"{profissional} ja tem atendimento em {data} as {hora}h"
            )

        atendimento = Atendimento(
            paciente, profissional, data, hora, duracao_minutos)
        self._atendimentos.append(atendimento)
        return atendimento

    def remarcar(self, paciente, data_atual, hora_atual, nova_data, nova_hora):
        """Remarca um atendimento existente para nova data e hora.

        Args:
            paciente (str): Nome do paciente cujo atendimento sera remarcado.
            data_atual (str): Data atual do atendimento, no formato
                AAAA-MM-DD.
            hora_atual (int): Hora atual do atendimento.
            nova_data (str): Nova data, no formato AAAA-MM-DD.
            nova_hora (int): Nova hora de inicio.

        Returns:
            Atendimento: O atendimento atualizado.

        Raises:
            ValueError: Se a nova data ou a nova hora forem invalidas.
            AtendimentoNaoEncontradoError: Se nao existir atendimento desse
                paciente na data e hora atuais informadas.
            HorarioIndisponivelError: Se o profissional ja tiver outro
                atendimento na nova data e hora.
        """
        validar_data(nova_data)

        atendimento = self._buscar(paciente, data_atual, hora_atual)
        if atendimento is None:
            raise AtendimentoNaoEncontradoError(
                f"nao ha atendimento de {paciente!r} em {data_atual} as "
                f"{hora_atual}h para remarcar"
            )

        validar_hora_do_atendimento(nova_hora, atendimento.duracao_minutos)

        if existe_conflito_de_horario(
            self._atendimentos,
            atendimento.profissional,
            nova_data,
            nova_hora,
            ignorar=atendimento,
        ):
            raise HorarioIndisponivelError(
                f"{atendimento.profissional} ja tem atendimento em "
                f"{nova_data} as {nova_hora}h"
            )

        atendimento.data = nova_data
        atendimento.hora = nova_hora
        return atendimento

    def listar_do_dia(self, data):
        """Lista os atendimentos marcados em uma data.

        Args:
            data (str): Data a listar, no formato AAAA-MM-DD.

        Returns:
            list[Atendimento]: Atendimentos daquela data, na ordem em que
            foram marcados.

        Raises:
            ValueError: Se ``data`` nao estiver no formato AAAA-MM-DD.
        """
        validar_data(data)
        return [a for a in self._atendimentos if a.data == data]

    def _buscar(self, paciente, data, hora):
        """Procura um atendimento pelo paciente, data e hora atuais.

        Args:
            paciente (str): Nome do paciente.
            data (str): Data atual do atendimento.
            hora (int): Hora atual do atendimento.

        Returns:
            Atendimento | None: O atendimento encontrado, ou None se nao
            existir nenhum com esses dados.
        """
        for atendimento in self._atendimentos:
            if (
                atendimento.paciente == paciente
                and atendimento.data == data
                and atendimento.hora == hora
            ):
                return atendimento
        return None


def _marcar_e_informar(
        agenda, paciente, profissional, data, hora, duracao_minutos):
    """Marca um atendimento e imprime o resultado para quem opera a agenda.

    Esta funcao e a unica responsavel por imprimir o resultado de uma
    marcacao; Agenda.marcar nunca imprime nada.

    Args:
        agenda (Agenda): Agenda em que o atendimento sera marcado.
        paciente (str): Nome do paciente.
        profissional (str): Nome do profissional.
        data (str): Data do atendimento, no formato AAAA-MM-DD.
        hora (int): Hora de inicio do atendimento.
        duracao_minutos (int): Duracao do atendimento, em minutos.
    """
    try:
        agenda.marcar(paciente, profissional, data, hora, duracao_minutos)
    except HorarioIndisponivelError:
        print("Horario ocupado")
    else:
        print("Atendimento marcado para", paciente)


def _remarcar_e_informar(
        agenda, paciente, data_atual, hora_atual, nova_data, nova_hora):
    """Remarca um atendimento e imprime o resultado para quem opera a agenda.

    Args:
        agenda (Agenda): Agenda onde o atendimento sera remarcado.
        paciente (str): Nome do paciente cujo atendimento sera remarcado.
        data_atual (str): Data atual do atendimento, no formato AAAA-MM-DD.
        hora_atual (int): Hora atual do atendimento.
        nova_data (str): Nova data, no formato AAAA-MM-DD.
        nova_hora (int): Nova hora de inicio.
    """
    try:
        agenda.remarcar(paciente, data_atual, hora_atual, nova_data, nova_hora)
    except HorarioIndisponivelError:
        print("Horario ocupado")
    else:
        print("Remarcado")


def _listar_e_imprimir(agenda, data):
    """Lista os atendimentos de uma data e os imprime, um por linha.

    Args:
        agenda (Agenda): Agenda a consultar.
        data (str): Data a listar, no formato AAAA-MM-DD.
    """
    for atendimento in agenda.listar_do_dia(data):
        print(
            atendimento.hora,
            atendimento.paciente,
            atendimento.profissional,
            atendimento.status,
        )


def executar_demonstracao():
    """Reproduz o cenario de demonstracao do agenda_base.py.

    Marca tres atendimentos (um deles em conflito de horario), remarca um
    deles e lista o dia. A saida impressa e identica a do codigo-base:
    "Atendimento marcado para Ana", "Horario ocupado", "Atendimento marcado
    para Carla", "Remarcado" e "14 Carla Dra. Souza MARCADO".
    """
    agenda = Agenda()
    _marcar_e_informar(agenda, "Ana", "Dr. Silva", "2026-10-05", 9, 30)
    _marcar_e_informar(agenda, "Bruno", "Dr. Silva", "2026-10-05", 9, 30)
    _marcar_e_informar(agenda, "Carla", "Dra. Souza", "2026-10-05", 14, 60)
    _remarcar_e_informar(agenda, "Ana", "2026-10-05", 9, "2026-10-06", 10)
    _listar_e_imprimir(agenda, "2026-10-05")


if __name__ == "__main__":
    executar_demonstracao()
