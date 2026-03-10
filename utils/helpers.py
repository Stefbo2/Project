USER_NAME_LOOKUP = {}


def set_user_name_lookup(mapping: dict) -> None:
    USER_NAME_LOOKUP.clear()
    USER_NAME_LOOKUP.update(mapping)


def minimize_transactions(net_balances: dict) -> list[dict]:
    creditors = []
    debtors = []
    for user_id, balance in net_balances.items():
        if round(balance, 2) > 0:
            creditors.append([user_id, round(balance, 2)])
        elif round(balance, 2) < 0:
            debtors.append([user_id, round(-balance, 2)])

    creditors.sort(key=lambda item: item[1], reverse=True)
    debtors.sort(key=lambda item: item[1], reverse=True)
    settlements = []
    ci = 0
    di = 0

    while ci < len(creditors) and di < len(debtors):
        creditor_id, creditor_amount = creditors[ci]
        debtor_id, debtor_amount = debtors[di]
        settled = round(min(creditor_amount, debtor_amount), 2)
        settlements.append(
            {
                "from_user_id": debtor_id,
                "to_user_id": creditor_id,
                "from_name": USER_NAME_LOOKUP.get(debtor_id, f"User {debtor_id}"),
                "to_name": USER_NAME_LOOKUP.get(creditor_id, f"User {creditor_id}"),
                "amount": settled,
            }
        )
        creditors[ci][1] = round(creditor_amount - settled, 2)
        debtors[di][1] = round(debtor_amount - settled, 2)
        if creditors[ci][1] == 0:
            ci += 1
        if debtors[di][1] == 0:
            di += 1

    return settlements
