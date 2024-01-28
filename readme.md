make sure to build proto files before running for update player stats service to run
`python -m grpc_tools.protoc --proto_path=protos --python_out=rpc --grpc_python_out=rpc --pyi_out=rpc protos/*.proto`
