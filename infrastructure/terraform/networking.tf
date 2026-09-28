resource "aws_subnet" "private_a" {
  vpc_id                  = data.aws_vpc.existing.id
  cidr_block              = "172.31.96.0/20"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = false

  tags = {
    Name      = "banking-private-a"
    Project   = "banking-support"
    ManagedBy = "terraform"
    Tier      = "private"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id                  = data.aws_vpc.existing.id
  cidr_block              = "172.31.112.0/20"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = false

  tags = {
    Name      = "banking-private-b"
    Project   = "banking-support"
    ManagedBy = "terraform"
    Tier      = "private"
  }
}