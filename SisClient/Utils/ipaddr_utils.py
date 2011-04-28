import socket
import struct

def ip_addr_to_long_number(ip_addr):
    '''Converts a given IP address in dotted string format to a long-valued number.
    The conversion uses the network byte-order (big endian).
    
    Argument:
        ipaddr -- IP address as a dotted decimal string
    
    Returns:
        Long number representing the IP address.
    '''
    return struct.unpack('!L', socket.inet_aton(ip_addr))[0]

def matches_ip_prefix(ip_addr, reference_ip_addr):
    '''Checks if a given IP address has the same prefix as the given reference IP address.
    The reference IP address contains the range of the prefix. Its format is: 192.168.2.1/4
    The 4 in this example means that the check is performed on the first 4 bits of both IP
    addresses.
    
    Arguments:
        ip_addr           -- IP address in dotted decimal format
        reference_ip_addr -- Reference IP address in dotted decimal format including information
                             on the actual size of the prefix bit range. Format: <IP>/<BITRANGE>
                             
    Returns:
        True, if the IP prefixes match. False, if the prefixes do not match or if the
        given reference IP does not comply to the expected format.
    '''
    if not is_reference_ip_addr_admissible(reference_ip_addr):
        return False
    ref_ip_addr, bitrange = _extract_addr_and_bitrange(reference_ip_addr)

    shifted_ref_ip_addr = _cut_off_irrelevant_bits(ip_addr_to_long_number(ref_ip_addr), bitrange)
    shifted_ip_addr = _cut_off_irrelevant_bits(ip_addr_to_long_number(ip_addr), bitrange)
    
    return (shifted_ref_ip_addr == shifted_ip_addr)

def is_reference_ip_addr_admissible(reference_ip_addr):
    return len(reference_ip_addr.split('/')) == 2

def _extract_addr_and_bitrange(reference_ip_addr):
    ref_ip_addr, ref_ip_bitrange = reference_ip_addr.split('/')
    return ref_ip_addr, int(ref_ip_bitrange)
    
def _cut_off_irrelevant_bits(ip_addr_as_long_number, bitrange):
    return ip_addr_as_long_number >> (32 - bitrange)

def validIP(address):
    parts = address.split(".")
    if len(parts) != 4:
        return False
    for item in parts:
        if not 0 <= int(item) <= 255:
            return False
    return True
