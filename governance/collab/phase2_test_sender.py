"""
Phase 2 Test Sender — simulates Nova sending a review_request to Jarvis.
Tests: event-driven dispatch + ACK return path.
Run from this machine or any machine on the LAN with nats-py installed.
"""

import asyncio
import json
import uuid
import sys
from datetime import datetime, timezone

from nats import connect


SUBJECTS = {
    'command': 'gov.collab.command',
    'ack': 'gov.collab.ack',
}


async def main():
    nats_url = sys.argv[1] if len(sys.argv) > 1 else "nats://192.168.31.64:4222"

    print(f"Connecting to {nats_url}...")
    nc = await connect(nats_url)
    print("Connected.")

    # Track ACKs received
    acks_received = []
    ack_event = asyncio.Event()

    async def handle_ack(msg):
        """Handler for inbound ACK messages."""
        data = json.loads(msg.data.decode('utf-8'))
        print(f"\n[ACK RECEIVED] message_id={data.get('message_id')} "
              f"ack_for={data.get('ack_for')} status={data.get('status')} "
              f"result={data.get('result')} to={data.get('to')} from={data.get('from')}")
        acks_received.append(data)
        ack_event.set()

    # Step 1: Subscribe to gov.collab.ack BEFORE publishing
    print("Subscribing to gov.collab.ack...")
    await nc.subscribe(SUBJECTS['ack'], cb=handle_ack)
    await nc.flush()
    print("Subscription active. Now publishing command.\n")

    # Step 2: Build and publish review_request
    collab_id = f"phase2-test-self-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    message_id = f"msg-{uuid.uuid4().hex[:12]}"

    envelope = {
        "message_id": message_id,
        "collab_id": collab_id,
        "message_type": "review_request",
        "from": "nova",
        "to": "jarvis",
        "artifact_type": "phase2_test",
        "artifact_path": __file__,
        "payload": {"test": True, "purpose": "phase2_ack_return_path"},
        "summary": "Phase 2 self-test: ACK return path verification",
        "protocol_version": "0.2",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    print(f"Publishing review_request: collab_id={collab_id} message_id={message_id}")
    await nc.publish(SUBJECTS['command'], json.dumps(envelope).encode('utf-8'))
    await nc.flush()
    print("Published. Waiting for ACK...\n")

    # Step 3: Wait for ACK with timeout
    try:
        await asyncio.wait_for(ack_event.wait(), timeout=10.0)
        print(f"\n[SUCCESS] ACK received within timeout")
        print(f"[SUCCESS] Total ACKs received: {len(acks_received)}")
        for a in acks_received:
            print(f"  -> ack_id={a.get('message_id')} status={a.get('status')} result={a.get('result')}")
    except asyncio.TimeoutError:
        print(f"\n[FAIL] No ACK received within 10 seconds")
        print(f"[FAIL] ACKs received before timeout: {len(acks_received)}")

    await nc.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())