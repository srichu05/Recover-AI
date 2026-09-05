"""
Synthetic Payment Environment & Incident Generator
Generates realistic synthetic merchant, customer, and transaction datasets with ground truth.
All amounts are in integer paise (1 INR = 100 paise).
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from backend.models import (
    Transaction, Customer, Incident, PaymentMethod,
    TransactionStatus, FailureCategory, IncidentType, IncidentSeverity
)

PROVIDERS = ["RAZORPAY_DIRECT", "HDFC_ROUTE", "ICICI_GATEWAY", "SBI_SWITCH", "AXIS_ROUTE"]
BANKS = ["HDFC", "ICICI", "SBI", "AXIS", "KOTAK"]
PAYMENT_METHODS = [PaymentMethod.UPI.value, PaymentMethod.CARD.value, PaymentMethod.NETBANKING.value, PaymentMethod.WALLET.value]

TRANSIENT_FAILURES = [
    "UPI_TIMEOUT",
    "GATEWAY_TIMEOUT",
    "NETWORK_DISCONNECT",
    "BANK_SWITCH_BUSY",
    "TEMPORARY_RATE_LIMIT"
]

PERMANENT_FAILURES = [
    "INVALID_ACCOUNT",
    "STOLEN_OR_BLOCKED_CARD",
    "ACCOUNT_CLOSED",
    "EXPIRED_CARD",
    "TRANSACTION_NOT_PERMITTED"
]

CUSTOMER_ACTION_FAILURES = [
    "INSUFFICIENT_FUNDS",
    "INCORRECT_PIN_OTP",
    "CUSTOMER_DROPOFF",
    "MANDATE_AUTH_FAILED"
]


def generate_synthetic_customers(count: int = 100, seed: Optional[int] = None) -> List[Customer]:
    """Generates synthetic customer payment profiles with historical metrics."""
    if seed is not None:
        random.seed(seed)
        
    first_names = ["Aarav", "Aditi", "Rahul", "Pooja", "Vikram", "Sneha", "Rohan", "Ananya", "Karan", "Divya",
                   "Arjun", "Neha", "Siddharth", "Meera", "Varun", "Rhea", "Nikhil", "Tanvi", "Amit", "Kavita"]
    last_names = ["Sharma", "Patel", "Verma", "Rao", "Gupta", "Nair", "Iyer", "Mehta", "Singh", "Joshi",
                  "Reddy", "Chopra", "Das", "Bhat", "Kapoor", "Saxena", "Menon", "Malhotra", "Deshmukh", "Pillai"]
    
    customers = []
    for i in range(count):
        cust_id = f"cust_{i+1:04d}"
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        payment_count = random.randint(3, 40)
        
        # 80% have good history, 15% medium, 5% low
        profile_rand = random.random()
        if profile_rand < 0.80:
            success_rate = round(random.uniform(0.85, 0.98), 2)
        elif profile_rand < 0.95:
            success_rate = round(random.uniform(0.65, 0.84), 2)
        else:
            success_rate = round(random.uniform(0.30, 0.60), 2)
            
        failure_count = max(0, int(payment_count * (1.0 - success_rate)))
        is_high_val = random.random() < 0.10
        
        customers.append(Customer(
            id=cust_id,
            name=f"{fn} {ln}",
            email=f"{fn.lower()}.{ln.lower()}{i+1}@example.com",
            phone=f"+9198{random.randint(10000000, 99999999)}",
            success_rate=success_rate,
            payment_count=payment_count,
            failure_count=failure_count,
            is_high_value=is_high_val
        ))
    return customers


def generate_baseline_transactions(
    count: int = 500,
    customers: Optional[List[Customer]] = None,
    seed: Optional[int] = None
) -> List[Transaction]:
    """Generates normal baseline traffic with expected ~93-95% success rate."""
    if seed is not None:
        random.seed(seed)
        
    if not customers:
        customers = generate_synthetic_customers(100, seed=seed)
        
    now = datetime.now()
    transactions = []
    
    for i in range(count):
        tx_id = f"pay_base_{uuid.uuid4().hex[:10]}"
        cust = random.choice(customers)
        t_delta = timedelta(minutes=random.randint(1, 120))
        tx_time = (now - t_delta).isoformat()
        
        # Method distribution: 65% UPI, 20% Card, 10% Netbanking, 5% Wallet
        m_rand = random.random()
        if m_rand < 0.65:
            method = PaymentMethod.UPI.value
            provider = random.choice(["RAZORPAY_DIRECT", "HDFC_ROUTE", "ICICI_GATEWAY"])
        elif m_rand < 0.85:
            method = PaymentMethod.CARD.value
            provider = random.choice(["HDFC_ROUTE", "ICICI_GATEWAY", "AXIS_ROUTE"])
        elif m_rand < 0.95:
            method = PaymentMethod.NETBANKING.value
            provider = random.choice(["SBI_SWITCH", "HDFC_ROUTE", "ICICI_GATEWAY"])
        else:
            method = PaymentMethod.WALLET.value
            provider = "RAZORPAY_DIRECT"
            
        bank = random.choice(BANKS)
        
        # Normal amount distribution in paise: ₹150 to ₹9,500 (15000 to 950000 paise)
        # 5% high-value ₹50,000+
        if random.random() < 0.05:
            amount_paise = random.randint(5500000, 12000000)  # ₹55,000 to ₹1,20,000
        else:
            amount_paise = random.randint(19900, 850000)  # ₹199 to ₹8,500
            
        # Success probability ~94%
        is_success = random.random() < 0.94
        
        if is_success:
            status = TransactionStatus.SUCCESS.value
            failure_reason = None
            failure_category = None
            is_transient = False
            gt_prob = 1.0
        else:
            status = TransactionStatus.FAILED.value
            fail_type_rand = random.random()
            if fail_type_rand < 0.70:
                failure_category = FailureCategory.TRANSIENT.value
                failure_reason = random.choice(TRANSIENT_FAILURES)
                is_transient = True
                gt_prob = 0.85
            elif fail_type_rand < 0.90:
                failure_category = FailureCategory.CUSTOMER_ACTION_REQUIRED.value
                failure_reason = random.choice(CUSTOMER_ACTION_FAILURES)
                is_transient = False
                gt_prob = 0.60
            else:
                failure_category = FailureCategory.PERMANENT.value
                failure_reason = random.choice(PERMANENT_FAILURES)
                is_transient = False
                gt_prob = 0.0
                
        transactions.append(Transaction(
            id=tx_id,
            merchant_id="merch_razor_01",
            customer_id=cust.id,
            timestamp=tx_time,
            amount_paise=amount_paise,
            currency="INR",
            payment_method=method,
            provider=provider,
            bank=bank,
            status=status,
            failure_reason=failure_reason,
            failure_category=failure_category,
            is_transient=is_transient,
            retry_count=0 if is_success else random.choice([0, 0, 1]),
            cart_value_paise=amount_paise,
            customer_success_rate=cust.success_rate,
            customer_payment_count=cust.payment_count,
            customer_failure_count=cust.failure_count,
            ground_truth_recovery_prob=gt_prob,
            is_recovered=False,
            recovered_amount_paise=0
        ))
    return transactions


def generate_incident_scenario(
    incident_type: IncidentType = IncidentType.UPI_TIMEOUT_SPIKE,
    severity_pct: float = 70.0,
    affected_count: int = 500,
    customers: Optional[List[Customer]] = None,
    seed: Optional[int] = None
) -> Tuple[Incident, List[Transaction]]:
    """
    Generates a controlled payment degradation incident and associated synthetic transactions
    with hidden ground truth for outcome evaluation.
    """
    if seed is not None:
        random.seed(seed)
        
    if not customers:
        customers = generate_synthetic_customers(150, seed=seed)
        
    now = datetime.now()
    incident_id = f"inc_{uuid.uuid4().hex[:8]}"
    
    transactions: List[Transaction] = []
    
    # Configure incident parameters based on scenario type
    if incident_type == IncidentType.UPI_TIMEOUT_SPIKE:
        title = "UPI Payment Route Latency & Timeout Spike"
        method = PaymentMethod.UPI.value
        provider = "RAZORPAY_DIRECT"
        bank = "HDFC"
        baseline_sr = 93.4
        degradation = (severity_pct / 100.0) * 35.0  # e.g., 70% severity = ~24.5% degradation
        current_sr = max(40.0, baseline_sr - degradation)
        primary_failure = "UPI_TIMEOUT"
        
    elif incident_type == IncidentType.PROVIDER_OUTAGE:
        title = "ICICI Gateway Network Disconnect Outage"
        method = PaymentMethod.CARD.value
        provider = "ICICI_GATEWAY"
        bank = "ICICI"
        baseline_sr = 95.0
        degradation = (severity_pct / 100.0) * 45.0
        current_sr = max(35.0, baseline_sr - degradation)
        primary_failure = "NETWORK_DISCONNECT"
        
    elif incident_type == IncidentType.BANK_SWITCH_DEGRADATION:
        title = "SBI Switch Intermittent Gateway Degradation"
        method = PaymentMethod.NETBANKING.value
        provider = "SBI_SWITCH"
        bank = "SBI"
        baseline_sr = 91.5
        degradation = (severity_pct / 100.0) * 30.0
        current_sr = max(50.0, baseline_sr - degradation)
        primary_failure = "BANK_SWITCH_BUSY"
        
    elif incident_type == IncidentType.MIXED_FAILURE_INCIDENT:
        title = "Multi-Vector Payment Processing Incident"
        method = "MIXED"
        provider = "MULTIPLE"
        bank = "MULTIPLE"
        baseline_sr = 94.0
        degradation = (severity_pct / 100.0) * 28.0
        current_sr = max(55.0, baseline_sr - degradation)
        primary_failure = "MIXED"
        
    else:  # NORMAL_TRAFFIC
        title = "Normal Payment Traffic Baseline"
        method = "ALL"
        provider = "ALL"
        bank = "ALL"
        baseline_sr = 94.2
        current_sr = 94.0
        degradation = 0.2
        primary_failure = "NONE"

    # Generate the transactions for this batch
    failure_target_count = int(affected_count * (1.0 - (current_sr / 100.0)))
    success_target_count = affected_count - failure_target_count
    
    # Generate successful transactions
    for _ in range(success_target_count):
        cust = random.choice(customers)
        tx_id = f"pay_inc_{uuid.uuid4().hex[:10]}"
        t_delta = timedelta(minutes=random.randint(1, 60))
        tx_time = (now - t_delta).isoformat()
        
        tx_method = method if method not in ("MIXED", "ALL") else random.choice(PAYMENT_METHODS)
        tx_provider = provider if provider not in ("MULTIPLE", "ALL") else random.choice(PROVIDERS)
        tx_bank = bank if bank not in ("MULTIPLE", "ALL") else random.choice(BANKS)
        amount_paise = random.randint(24900, 750000)  # ₹249 - ₹7,500
        
        transactions.append(Transaction(
            id=tx_id,
            merchant_id="merch_razor_01",
            customer_id=cust.id,
            timestamp=tx_time,
            amount_paise=amount_paise,
            currency="INR",
            payment_method=tx_method,
            provider=tx_provider,
            bank=tx_bank,
            status=TransactionStatus.SUCCESS.value,
            failure_reason=None,
            failure_category=None,
            is_transient=False,
            retry_count=0,
            cart_value_paise=amount_paise,
            customer_success_rate=cust.success_rate,
            customer_payment_count=cust.payment_count,
            customer_failure_count=cust.failure_count,
            ground_truth_recovery_prob=1.0,
            is_recovered=False,
            recovered_amount_paise=0,
            incident_id=incident_id
        ))

    # Generate failed transactions (The affected incident cohort)
    for idx in range(failure_target_count):
        cust = random.choice(customers)
        tx_id = f"pay_fail_{uuid.uuid4().hex[:10]}"
        t_delta = timedelta(minutes=random.randint(1, 60))
        tx_time = (now - t_delta).isoformat()
        
        tx_method = method if method not in ("MIXED", "ALL") else random.choice(PAYMENT_METHODS)
        tx_provider = provider if provider not in ("MULTIPLE", "ALL") else random.choice(PROVIDERS)
        tx_bank = bank if bank not in ("MULTIPLE", "ALL") else random.choice(BANKS)
        
        # Inject realistic failure distribution
        # In UPI Timeout incident: 75% UPI_TIMEOUT (transient), 15% Customer Action, 10% Permanent
        rand_val = random.random()
        
        # Inject ~5% high-value transactions (> ₹50,000) to test autonomous policy limit
        if idx % 20 == 0:
            amount_paise = random.randint(5200000, 11000000)  # ₹52,000 - ₹1,10,000 (Requires escalation)
        else:
            amount_paise = random.randint(19900, 1200000)  # ₹199 - ₹12,000
            
        # Inject ~8% with retry_count >= 2 to test MAX_RETRIES policy stop
        retry_count = 2 if (idx % 12 == 0) else (1 if (idx % 6 == 0) else 0)
        
        if rand_val < 0.72:
            failure_cat = FailureCategory.TRANSIENT.value
            fail_reason = primary_failure if primary_failure != "MIXED" else random.choice(TRANSIENT_FAILURES)
            is_transient = True
            
            # Ground truth: High if retry < 2 and good customer history, else low
            if retry_count >= 2:
                gt_prob = 0.0  # Policy will prevent retry anyway
            elif cust.success_rate >= 0.80:
                gt_prob = 0.90
            else:
                gt_prob = 0.70
                
        elif rand_val < 0.88:
            failure_cat = FailureCategory.CUSTOMER_ACTION_REQUIRED.value
            fail_reason = random.choice(CUSTOMER_ACTION_FAILURES)
            is_transient = False
            gt_prob = 0.65 if cust.success_rate >= 0.75 else 0.35
            
        else:
            failure_cat = FailureCategory.PERMANENT.value
            fail_reason = random.choice(PERMANENT_FAILURES)
            is_transient = False
            gt_prob = 0.0  # Permanent failure cannot recover via retry
            
        transactions.append(Transaction(
            id=tx_id,
            merchant_id="merch_razor_01",
            customer_id=cust.id,
            timestamp=tx_time,
            amount_paise=amount_paise,
            currency="INR",
            payment_method=tx_method,
            provider=tx_provider,
            bank=tx_bank,
            status=TransactionStatus.FAILED.value,
            failure_reason=fail_reason,
            failure_category=failure_cat,
            is_transient=is_transient,
            retry_count=retry_count,
            cart_value_paise=amount_paise,
            customer_success_rate=cust.success_rate,
            customer_payment_count=cust.payment_count,
            customer_failure_count=cust.failure_count,
            ground_truth_recovery_prob=gt_prob,
            is_recovered=False,
            recovered_amount_paise=0,
            incident_id=incident_id
        ))

    # Shuffle transactions so successes and failures are mixed naturally in time
    random.shuffle(transactions)
    
    # Calculate aggregate financial and exposure metrics
    total_volume_paise = sum(t.amount_paise for t in transactions)
    failed_txs = [t for t in transactions if t.status == TransactionStatus.FAILED.value]
    
    # Revenue at risk: Unsuccessful transactions with plausible recovery path
    revenue_at_risk_paise = sum(
        t.amount_paise for t in failed_txs 
        if t.failure_category in (FailureCategory.TRANSIENT.value, FailureCategory.CUSTOMER_ACTION_REQUIRED.value)
    )
    
    # Estimated recoverable paise based on ground truth expectations
    estimated_recoverable_paise = int(sum(
        t.amount_paise * t.ground_truth_recovery_prob for t in failed_txs
    ))

    # Determine severity label
    sev_pct_calc = round(100.0 - current_sr, 1)
    if sev_pct_calc >= 30.0:
        sev_label = IncidentSeverity.CRITICAL.value
    elif sev_pct_calc >= 20.0:
        sev_label = IncidentSeverity.HIGH.value
    elif sev_pct_calc >= 10.0:
        sev_label = IncidentSeverity.MEDIUM.value
    else:
        sev_label = IncidentSeverity.LOW.value

    incident = Incident(
        id=incident_id,
        title=title,
        incident_type=incident_type.value if hasattr(incident_type, "value") else str(incident_type),
        payment_method=method,
        status="ACTIVE",
        severity=sev_label,
        severity_pct=severity_pct,
        affected_count=len(failed_txs),
        baseline_success_rate=round(baseline_sr, 2),
        current_success_rate=round(current_sr, 2),
        degradation_pct=round(baseline_sr - current_sr, 2),
        total_volume_paise=total_volume_paise,
        revenue_at_risk_paise=revenue_at_risk_paise,
        estimated_recoverable_paise=estimated_recoverable_paise,
        actual_recovered_paise=0,
        baseline_recovered_paise=0,
        created_at=now.isoformat(),
        metadata={
            "provider": provider,
            "bank": bank,
            "primary_failure": primary_failure,
            "total_transactions": len(transactions),
            "failed_count": len(failed_txs)
        }
    )
    
    return incident, transactions
