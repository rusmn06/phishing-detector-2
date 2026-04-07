import dns.resolver
from typing import Optional
from config import settings

def create_resilient_resolver(timeout: float = None) -> dns.resolver.Resolver:
    """
    Membuat DNS resolver dengan timeout yang dikonfigurasi + fallback ke public DNS.
    """
    if timeout is None:
        timeout = float(settings.DNS_TIMEOUT)  # Default dari .env
    
    resolver = dns.resolver.Resolver()
    
    # Timeout yang lebih longgar
    resolver.timeout = timeout
    resolver.lifetime = timeout * 3  # Total waktu untuk semua retry
    
    # Fallback ke public DNS jika nameserver default bermasalah
    # Prioritas: Google DNS → Cloudflare → OpenDNS
    resolver.nameservers = [
        '8.8.8.8',    # Google
        '8.8.4.4',    # Google Secondary
        '1.1.1.1',    # Cloudflare
        '1.0.0.1',    # Cloudflare Secondary
    ]
    
    return resolver