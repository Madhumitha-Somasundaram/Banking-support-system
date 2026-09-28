
# ---------------------------------------------------------
# Elastic IP for NAT Gateway
# ---------------------------------------------------------

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name      = "banking-nat-eip"
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ---------------------------------------------------------
# NAT Gateway
# ---------------------------------------------------------

resource "aws_nat_gateway" "banking" {
  allocation_id = aws_eip.nat.id

  # Existing public subnet
  subnet_id = "subnet-0a3f8d4d1d6c4fdc8"

  tags = {
    Name      = "banking-nat-gateway"
    Project   = "banking-support"
    ManagedBy = "terraform"
  }

  depends_on = [
    aws_eip.nat
  ]
}


# ---------------------------------------------------------
# Private Route Table
# ---------------------------------------------------------

resource "aws_route_table" "private" {
  vpc_id = data.aws_vpc.existing.id

  tags = {
    Name      = "banking-private-rt"
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ---------------------------------------------------------
# Route private subnet traffic through NAT
# ---------------------------------------------------------

resource "aws_route" "private_nat" {
  route_table_id = aws_route_table.private.id

  destination_cidr_block = "0.0.0.0/0"

  nat_gateway_id = aws_nat_gateway.banking.id
}



resource "aws_route_table_association" "private_a" {
  subnet_id      = var.private_subnets[0]
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_b" {
  subnet_id      = var.private_subnets[1]
  route_table_id = aws_route_table.private.id
}
