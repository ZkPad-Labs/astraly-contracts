from tracemalloc import start
import pytest
from utils import *
from starkware.starknet.definitions.error_codes import StarknetErrorCode
from starkware.starkware_utils.error_handling import StarkException
from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.public.abi import get_selector_from_name
from datetime import datetime, date, timedelta
from conftest import get_block_timestamp, set_block_timestamp
from pprint import pprint as pp

TRUE = 1
FALSE = 0
NAME = str_to_felt("ZkPad")
SYMBOL = str_to_felt("ZKP")
DECIMALS = 18
INIT_SUPPLY = to_uint(1000)
CAP = to_uint(1000)
RND_NBR_GEN_SEED = 76823
TOKEN_ID = uint(0)
MINT_AMOUNT = uint(1000)
ONE_DAY = 24 * 60 * 60

account_path = 'openzeppelin/account/Account.cairo'
ido_factory_path = 'mocks/ZkPadIDOFactory_mock.cairo'
rnd_nbr_gen_path = 'utils/xoroshiro128_starstar.cairo'
erc1155_path = 'ZkPadLotteryToken.cairo'
erc20_eth_path = 'mocks/ZkPad_ETH_ERC20_mock.cairo'

deployer = Signer(1234321)
admin1 = Signer(2345432)
staking = Signer(3456543)
sale_owner = Signer(4567654)
sale_participant = Signer(5678765)
sale_participant_2 = Signer(678909876)
zkp_recipient = Signer(123456789987654321)
zkp_owner = Signer(123456789876543210)


def advance_clock(starknet_state, num_seconds):
    set_block_timestamp(
        starknet_state, get_block_timestamp(
            starknet_state) + num_seconds
    )


def days_to_seconds(days: int):
    return days * 24 * 60 * 60


@pytest.fixture(scope='module')
async def get_starknet():
    starknet = await Starknet.empty()
    set_block_timestamp(starknet.state, int(
        datetime.today().timestamp()))  # time.time()
    return starknet


@pytest.fixture(scope='module')
def contract_defs():
    account_def = get_contract_def(account_path)
    zk_pad_admin_def = get_contract_def('ZkPadAdmin.cairo')
    zk_pad_ido_factory_def = get_contract_def(ido_factory_path)
    rnd_nbr_gen_def = get_contract_def(rnd_nbr_gen_path)
    erc1155_def = get_contract_def(erc1155_path)
    zk_pad_ido_def = get_contract_def('ZkPadIDOContract.cairo')
    zk_pad_token_def = get_contract_def('ZkPadToken.cairo')
    task_def = get_contract_def('ZkPadTask.cairo')
    erc20_eth_def = get_contract_def(erc20_eth_path)

    return account_def, zk_pad_admin_def, zk_pad_ido_factory_def, rnd_nbr_gen_def, erc1155_def, zk_pad_ido_def, zk_pad_token_def, task_def, erc20_eth_def

@pytest.fixture(scope='module')
async def contacts_init(contract_defs, get_starknet):
    starknet = get_starknet
    account_def, zk_pad_admin_def, zk_pad_ido_factory_def, rnd_nbr_gen_def, erc1155_def, zk_pad_ido_def, zk_pad_token_def, task_def, erc20_eth_def = contract_defs

    deployer_account = await starknet.deploy(
        contract_def=account_def,
        constructor_calldata=[deployer.public_key]
    )
    admin1_account = await starknet.deploy(
        contract_def=account_def,
        constructor_calldata=[admin1.public_key]
    )
    staking_account = await starknet.deploy(
        contract_def=account_def,
        constructor_calldata=[staking.public_key]
    )
    sale_owner_account = await starknet.deploy(
        contract_def=account_def,
        constructor_calldata=[sale_owner.public_key]
    )

    sale_participant_account = await starknet.deploy(
        contract_def=account_def,
        constructor_calldata=[sale_participant.public_key]
    )

    sale_participant_2_account = await starknet.deploy(
        contract_def=account_def,
        constructor_calldata=[sale_participant_2.public_key]
    )

    zkp_recipient_account = await starknet.deploy(
        contract_def=account_def,
        constructor_calldata=[zkp_recipient.public_key]
    )

    zkp_owner_account = await starknet.deploy(
        contract_def=account_def,
        constructor_calldata=[zkp_owner.public_key]
    )

    zk_pad_admin = await starknet.deploy(
        contract_def=zk_pad_admin_def,
        constructor_calldata=[
            1,
            *[admin1_account.contract_address]
        ],
    )

    rnd_nbr_gen = await starknet.deploy(
        contract_def=rnd_nbr_gen_def,
        constructor_calldata=[RND_NBR_GEN_SEED],
    )

    zk_pad_ido_factory = await starknet.deploy(
        contract_def=zk_pad_ido_factory_def,
        constructor_calldata=[],
    )

    erc1155 = await starknet.deploy(
        contract_def=erc1155_def,
        constructor_calldata=[
            0, deployer_account.contract_address, zk_pad_ido_factory.contract_address]
    )

    await deployer.send_transaction(
        deployer_account, zk_pad_ido_factory.contract_address, 'set_random_number_generator_address',
        [rnd_nbr_gen.contract_address]
    )

    zk_pad_token = await starknet.deploy(
        contract_def=zk_pad_token_def,
        constructor_calldata=[
            NAME,
            SYMBOL,
            DECIMALS,
            *INIT_SUPPLY,
            zkp_recipient_account.contract_address,        # recipient
            zkp_owner_account.contract_address,
            *CAP,
            123124
        ],
    )

    zk_pad_ido = await starknet.deploy(
        contract_def=zk_pad_ido_def,
        constructor_calldata=[
            zk_pad_admin.contract_address,
            staking_account.contract_address,
            zk_pad_ido_factory.contract_address
        ],
    )

    task = await starknet.deploy(
        contract_def=task_def,
        constructor_calldata=[
            zk_pad_ido_factory.contract_address,
        ],
    )

    await deployer.send_transaction(deployer_account, zk_pad_ido_factory.contract_address, "set_task_address",
                                    [task.contract_address])

    await deployer.send_transaction(deployer_account, zk_pad_ido_factory.contract_address, "create_ido", [zk_pad_ido.contract_address])

    await deployer.send_transaction(deployer_account, zk_pad_ido_factory.contract_address, "set_lottery_ticket_contract_address",
                                    [erc1155.contract_address])

    erc20_eth_token = await starknet.deploy(
        contract_def=erc20_eth_def,
        constructor_calldata=[
            deployer_account.contract_address,
            deployer_account.contract_address
        ],
    )

    await deployer.send_transaction(deployer_account, erc20_eth_token.contract_address, "transfer", 
        [sale_participant_account.contract_address, *to_uint(10000)]
    )

    await deployer.send_transaction(deployer_account, erc20_eth_token.contract_address, "transfer", 
        [sale_participant_2_account.contract_address, *to_uint(5000)]
    )

    await deployer.send_transaction(
        deployer_account, 
        zk_pad_ido_factory.contract_address,
        "set_payment_token_address",
        [erc20_eth_token.contract_address])

    return (
        deployer_account,
        admin1_account,
        staking_account,
        sale_owner_account,
        sale_participant_account,
        sale_participant_2_account,
        zkp_recipient_account,
        zkp_owner_account,
        zk_pad_admin,
        rnd_nbr_gen,
        zk_pad_ido_factory,
        erc1155,
        zk_pad_token,
        zk_pad_ido,
        erc20_eth_token
    )


@pytest.fixture
def contracts_factory(contract_defs, contacts_init, get_starknet):
    account_def, zk_pad_admin_def, rnd_nbr_gen_def, erc1155_def, zk_pad_ido_factory_def, zk_pad_ido_def, zk_pad_token_def, task_def, erc20_eth_def = contract_defs
    deployer_account, admin1_account, staking_account, sale_owner_account, sale_participant_account, sale_participant_2_account, _, _, zk_pad_admin, rnd_nbr_gen, zk_pad_ido_factory, erc1155, zk_pad_token, zk_pad_ido, erc20_eth_token = contacts_init
    _state = get_starknet.state.copy()
    admin_cached = cached_contract(_state, zk_pad_admin_def, zk_pad_admin)
    deployer_cached = cached_contract(_state, account_def, deployer_account)
    admin1_cached = cached_contract(_state, account_def, admin1_account)
    staking_cached = cached_contract(_state, account_def, staking_account)
    owner_cached = cached_contract(_state, account_def, sale_owner_account)
    participant_cached = cached_contract(
        _state, account_def, sale_participant_account)
    participant_2_cached = cached_contract(
        _state, account_def, sale_participant_2_account)
    zkp_token_cached = cached_contract(_state, zk_pad_token_def, zk_pad_token)
    ido_cached = cached_contract(_state, zk_pad_ido_def, zk_pad_ido)
    rnd_nbr_gen_cached = cached_contract(_state, rnd_nbr_gen_def, rnd_nbr_gen)
    ido_factory_cached = cached_contract(
        _state, zk_pad_ido_factory_def, zk_pad_ido_factory)
    erc1155_cached = cached_contract(_state, erc1155_def, erc1155)
    erc20_eth_token_cached = cached_contract(_state, erc20_eth_def, erc20_eth_token)
    return admin_cached, deployer_cached, admin1_cached, staking_cached, owner_cached, participant_cached, participant_2_cached, zkp_token_cached, ido_cached, rnd_nbr_gen_cached, ido_factory_cached, erc1155_cached, erc20_eth_token_cached, _state


@pytest.mark.asyncio
async def test_setup_sale_success_with_events(contracts_factory):
    zkpad_admin_account, deployer_account, admin_user, stakin_contract, owner, participant, participant_2, zkp_token, ido, rnd_nbr_gen, ido_factory, erc1155, erc20_eth_token, starknet_state = contracts_factory
    day = datetime.today()
    timeDelta90days = timedelta(days=90)
    timeDeltaOneWeek = timedelta(weeks=1)
    timeDeltaOneDay = timedelta(days=1)

    sale_end = day + timeDelta90days
    token_unlock = sale_end + timeDeltaOneWeek
    
    tx = await admin1.send_transaction(
        admin_user,
        ido.contract_address,
        "set_sale_params",
        [
            zkp_token.contract_address,
            owner.contract_address,
            *to_uint(100),
            *to_uint(1000000),
            int(sale_end.timestamp()),
            int(token_unlock.timestamp()),
            *to_uint(1000),
            *to_uint(10000)
        ]
    )

    assert_event_emitted(tx, ido.contract_address, "sale_created", data=[
        owner.contract_address,
        *to_uint(100),
        *to_uint(1000000),
        int(sale_end.timestamp()),
        int(token_unlock.timestamp())
    ])

    reg_start = day + timeDeltaOneDay
    reg_end = reg_start + timeDeltaOneWeek

    tx = await admin1.send_transaction(
        admin_user,
        ido.contract_address,
        "set_registration_time",
        [
            int(reg_start.timestamp()),
            int(reg_end.timestamp())
        ]
    )

    assert_event_emitted(tx, ido.contract_address, "registration_time_set", data=[
        int(reg_start.timestamp()),
        int(reg_end.timestamp())
    ])

    purchase_round_start = reg_end + timeDeltaOneDay
    purchase_round_end = purchase_round_start + timeDeltaOneWeek

    tx = await admin1.send_transaction(
        admin_user,
        ido.contract_address,
        "set_purchase_round_params",
        [
            int(purchase_round_start.timestamp()),
            int(purchase_round_end.timestamp())
        ]
    )

    assert_event_emitted(tx, ido.contract_address, "purchase_round_time_set", data=[
        int(purchase_round_start.timestamp()),
        int(purchase_round_end.timestamp())
    ])

    dist_round_start = purchase_round_end + timeDeltaOneDay

    tx = await admin1.send_transaction(
        admin_user,
        ido.contract_address,
        "set_dist_round_params",
        [
            int(dist_round_start.timestamp())
        ]
    )

    assert_event_emitted(tx, ido.contract_address, "distribtion_round_time_set", data=[
        int(dist_round_start.timestamp())
    ])

    await deployer.send_transaction(
        deployer_account,
        erc1155.contract_address,
        'mint',
        [
            participant.contract_address,
            *TOKEN_ID,
            *MINT_AMOUNT,
            0  # data
        ]
    )

    advance_clock(starknet_state, days_to_seconds(2) + 1)

    burn_from = participant.contract_address
    tx = await sale_participant.send_transaction(
        participant,
        erc1155.contract_address,
        'burn',
        [
            burn_from,
            *TOKEN_ID,
            *MINT_AMOUNT
        ]
    )
    pp(tx.raw_events)

    my_event = next((x for x in tx.raw_events if get_selector_from_name(
        "user_registered") in x.keys), None)
    pp(my_event)
    assert my_event is not None

    await deployer.send_transaction(
        deployer_account,
        erc1155.contract_address,
        'mint',
        [
            participant_2.contract_address,
            *TOKEN_ID,
            *MINT_AMOUNT,
            0  # data
        ]
    )

    tx = await sale_participant_2.send_transaction(
        participant_2,
        erc1155.contract_address,
        'burn',
        [
            participant_2.contract_address,
            *TOKEN_ID,
            *MINT_AMOUNT
        ]
    )

    my_event = next((x for x in tx.raw_events if get_selector_from_name(
        "user_registered") in x.keys), None)
    pp(my_event)
    assert my_event is not None

    # advance block timestamp to be inside the purchase round
    # advance_clock(starknet_state, days_to_seconds(7) + 1)
    set_block_timestamp(starknet_state, int(purchase_round_start.timestamp()) + 60)

    # calculate the allocation
    tx = await admin1.send_transaction(
        admin_user,
        ido.contract_address,
        "calculate_allocation",
        []
    )

    # sale participant 1
    tx = await sale_participant.send_transaction(
        participant,
        erc20_eth_token.contract_address,
        'approve',
        [
            ido.contract_address,
            *to_uint(2000)    
        ]
    )

    tx = await sale_participant.send_transaction(
        participant,
        ido.contract_address,
        'participate',
        [
            participant.contract_address,
            *to_uint(2000)
        ]
    )

    # sale participant 2
    tx = await sale_participant_2.send_transaction(
        participant_2,
        erc20_eth_token.contract_address,
        'approve',
        [
            ido.contract_address,
            *to_uint(2000)    
        ]
    )

    tx = await sale_participant_2.send_transaction(
        participant_2,
        ido.contract_address,
        'participate',
        [
            participant_2.contract_address,
            *to_uint(1000)
        ]
    )